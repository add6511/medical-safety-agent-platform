import { prisma } from "@/Lib/Prisma";
import { AppError } from "@/Middleware/ErrorHandler";
import { validatePagination } from "@/Lib/Validator";
import { PlanStatus, TaskStatus, VisitStatus } from "@prisma/client";

export async function createFollowupPlan(
  followerUserId: string,
  data: {
    patientId: string;
    visitId: string;
    frequency: string;
    startDate: string;
    endDate: string;
  }
) {
  const visit = await prisma.visit.findUnique({
    where: { visitId: data.visitId },
  });
  if (!visit || visit.status !== VisitStatus.confirmed) {
    throw new AppError("对应就诊记录必须已确认", 422);
  }

  const existingPlan = await prisma.followupPlan.findFirst({
    where: { patientId: data.patientId, status: PlanStatus.active },
  });
  if (existingPlan) {
    throw new AppError("该患者已有活跃随访计划", 409);
  }

  const startDate = new Date(data.startDate);
  const endDate = new Date(data.endDate);
  if (endDate <= startDate) {
    throw new AppError("结束日期必须晚于开始日期", 422);
  }

  const plan = await prisma.followupPlan.create({
    data: {
      patientId: data.patientId,
      visitId: data.visitId,
      frequency: data.frequency as never,
      startDate,
      endDate,
      status: PlanStatus.active,
      creatorId: followerUserId,
    },
  });

  const tasks = await generateFollowupTasks(
    plan.planId,
    data.frequency,
    startDate,
    endDate
  );

  return { planId: plan.planId, tasks };
}

export async function generateFollowupTasks(
  planId: string,
  frequency: string,
  startDate: Date,
  endDate: Date
) {
  const intervalDays: Record<string, number> = {
    weekly: 7,
    biweekly: 14,
    monthly: 30,
    quarterly: 90,
  };

  const days = intervalDays[frequency] || 30;
  const tasks: Array<{ taskId: string; plannedDate: string; status: string }> =
    [];

  const currentDate = new Date(startDate);
  while (currentDate <= endDate) {
    const task = await prisma.followupTask.create({
      data: {
        planId,
        plannedDate: new Date(currentDate),
        status: TaskStatus.pending,
      },
    });
    tasks.push({
      taskId: task.taskId,
      plannedDate: task.plannedDate.toISOString(),
      status: task.status,
    });
    currentDate.setDate(currentDate.getDate() + days);
  }

  return tasks;
}

export async function getFollowupPlanList(
  userId: string,
  role: string,
  query: { status?: string; page?: number; pageSize?: number }
) {
  const { page, pageSize } = validatePagination(query.page, query.pageSize);

  const where: Record<string, unknown> = {};
  if (query.status) where.status = query.status;

  if (role === "follower") {
    where.creatorId = userId;
  } else if (role === "patient") {
    const patient = await prisma.simulatedPatient.findUnique({
      where: { userId },
    });
    if (patient) where.patientId = patient.patientId;
  }

  const [total, items] = await Promise.all([
    prisma.followupPlan.count({ where }),
    prisma.followupPlan.findMany({
      where,
      orderBy: { startDate: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
      include: { tasks: true },
    }),
  ]);

  return { total, page, pageSize, items };
}

export async function getFollowupPlanDetail(
  planId: string,
  _userId: string,
  _role: string
) {
  const plan = await prisma.followupPlan.findUnique({
    where: { planId },
    include: { tasks: { orderBy: { plannedDate: "asc" } } },
  });
  if (!plan) {
    throw new AppError("随访计划不存在", 404);
  }
  return plan;
}

export async function terminateFollowupPlan(
  planId: string,
  followerUserId: string,
  terminateReason: string
) {
  const plan = await prisma.followupPlan.findUnique({
    where: { planId },
  });
  if (!plan) {
    throw new AppError("随访计划不存在", 404);
  }
  if (plan.status !== PlanStatus.active) {
    throw new AppError("仅活跃计划可终止", 409);
  }

  const cancelResult = await prisma.followupTask.updateMany({
    where: {
      planId,
      status: { in: [TaskStatus.pending, TaskStatus.reminded] },
    },
    data: { status: TaskStatus.cancelled },
  });

  await prisma.followupPlan.update({
    where: { planId },
    data: {
      status: PlanStatus.terminated,
      terminateReason,
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: followerUserId,
      action: "review_return",
      targetType: "followup_plan",
      targetId: planId,
      detail: { terminateReason, cancelledTaskCount: cancelResult.count },
    },
  });

  return {
    planId,
    status: "terminated" as const,
    cancelledTaskCount: cancelResult.count,
  };
}

export async function completeFollowupTask(
  taskId: string,
  followerUserId: string,
  resultNote: string
) {
  if (!resultNote || resultNote.length > 2000) {
    throw new AppError("随访结果必填且最大2000字符", 422);
  }

  const medicationPattern = /用药调整|药物调整|换药|加药|减药/;
  if (medicationPattern.test(resultNote)) {
    throw new AppError("随访结果不可包含用药调整指导", 422);
  }

  const task = await prisma.followupTask.findUnique({ where: { taskId } });
  if (!task) {
    throw new AppError("随访任务不存在", 404);
  }
  if (task.status !== TaskStatus.pending && task.status !== TaskStatus.reminded) {
    throw new AppError("仅待执行或已提醒的任务可完成", 409);
  }

  const updated = await prisma.followupTask.update({
    where: { taskId },
    data: {
      status: TaskStatus.completed,
      completionDate: new Date(),
      resultNote,
      executorId: followerUserId,
    },
  });

  return {
    taskId,
    status: "completed" as const,
    completionDate: updated.completionDate!.toISOString(),
  };
}

export async function getMyFollowupTasks(patientUserId: string) {
  const patient = await prisma.simulatedPatient.findUnique({
    where: { userId: patientUserId },
  });
  if (!patient) {
    throw new AppError("患者记录不存在", 404);
  }

  const plans = await prisma.followupPlan.findMany({
    where: { patientId: patient.patientId, status: PlanStatus.active },
    include: {
      tasks: {
        where: {
          status: { in: [TaskStatus.pending, TaskStatus.reminded] },
        },
        orderBy: { plannedDate: "asc" },
      },
    },
  });

  return plans.flatMap((p) => p.tasks);
}

export async function processOverdueTasks() {
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  const result = await prisma.followupTask.updateMany({
    where: {
      plannedDate: { lt: sevenDaysAgo },
      status: { in: [TaskStatus.pending, TaskStatus.reminded] },
    },
    data: { status: TaskStatus.overdue },
  });

  return { overdueCount: result.count };
}