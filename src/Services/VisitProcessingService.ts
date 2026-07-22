import { prisma } from "@/Lib/Prisma";
import { VisitStatus, ReviewStatus } from "@prisma/client";
import { AppError } from "@/Middleware/ErrorHandler";
import { validatePagination } from "@/Lib/Validator";
import { executePreScreening } from "./RuleEngineService";
import { riskReview, getCurrentModelConfig } from "./AIClientService";
import { reviewAIOutput } from "./SafetyAgentService";

export async function processVisitSubmission(visitId: string) {
  let preScreenResult;
  try {
    preScreenResult = await executePreScreening(visitId);
  } catch {
    await prisma.visit.update({
      where: { visitId },
      data: { status: VisitStatus.pending_review, riskLevel: "pending" },
    });
    await prisma.safetyAlert.create({
      data: {
        alertType: "unauthorized_diagnosis",
        severity: "info",
        sourceType: "system_check",
        sourceId: visitId,
        detail: { message: "规则引擎执行失败，标记待人工筛查" },
      },
    });
    return { visitId, status: "pending_review", degraded: true };
  }

  const modelConfig = await getCurrentModelConfig();
  let aiResult = null;
  let safetyCheckPassed = true;
  let finalAiOutput = null;

  try {
    aiResult = await riskReview(
      { visitId, symptoms: preScreenResult.redFlagResults },
      preScreenResult
    );

    if (aiResult) {
      const safetyResult = await reviewAIOutput(
        JSON.stringify(aiResult),
        visitId
      );

      if (safetyResult.status === "blocked") {
        safetyCheckPassed = false;
      } else {
        finalAiOutput = safetyResult.processedOutput;
        if (safetyResult.status === "replaced") {
          safetyCheckPassed = true;
        }
      }
    }
  } catch {
    safetyCheckPassed = false;
  }

  const triageResult = await prisma.triageResult.create({
    data: {
      visitId,
      riskLevel: preScreenResult.riskLevel,
      riskEvidence: {
        redFlagResults: preScreenResult.redFlagResults,
        contraindicationResults: preScreenResult.contraindicationResults,
      },
      ruleVersion: preScreenResult.ruleVersion,
      aiOutput: finalAiOutput ? JSON.parse(finalAiOutput) : { degraded: true },
      safetyCheckPassed,
      reviewStatus: ReviewStatus.pending,
    },
  });

  if (modelConfig) {
    await prisma.agentRun.create({
      data: {
        visitId,
        modelVersion: modelConfig.modelVersion,
        promptVersion: modelConfig.promptVersion,
        knowledgeBaseVersion: modelConfig.knowledgeBaseVersion,
        inputContent: { visitId },
        outputContent: aiResult || { degraded: true },
        safetyCheckResult: { passed: safetyCheckPassed },
      },
    });
  }

  await prisma.visit.update({
    where: { visitId },
    data: { status: VisitStatus.pending_review, riskLevel: preScreenResult.riskLevel },
  });

  return { visitId, triageId: triageResult.triageId };
}

export async function getPendingReviewList(
  _doctorUserId: string,
  query: { page?: number; pageSize?: number }
) {
  const { page, pageSize } = validatePagination(query.page, query.pageSize);

  const where = { reviewStatus: ReviewStatus.pending };

  const [total, items] = await Promise.all([
    prisma.triageResult.count({ where }),
    prisma.triageResult.findMany({
      where,
      orderBy: { riskLevel: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
      include: { visit: { include: { symptoms: true } } },
    }),
  ]);

  return { total, page, pageSize, items };
}

export async function getTriageDetail(triageId: string, userId: string, role: string) {
  const triage = await prisma.triageResult.findUnique({
    where: { triageId },
    include: {
      visit: { include: { symptoms: true, agentRuns: { include: { citations: true } } } },
    },
  });
  if (!triage) {
    throw new AppError("分诊结果不存在", 404);
  }
  if (role === "patient") {
    throw new AppError("患者无权查看风险评定详情", 403);
  }
  return triage;
}

export async function reviewTriage(
  triageId: string,
  doctorUserId: string,
  action: "confirm" | "return" | "flag",
  reviewComment?: string
) {
  const triage = await prisma.triageResult.findUnique({
    where: { triageId },
  });
  if (!triage) {
    throw new AppError("分诊结果不存在", 404);
  }
  if (triage.reviewStatus !== ReviewStatus.pending) {
    throw new AppError("该分诊结果已被审核", 409);
  }
  if (action === "return" && !reviewComment) {
    throw new AppError("退回时审核意见必填", 422);
  }

  const reviewStatusMap = {
    confirm: ReviewStatus.confirmed,
    return: ReviewStatus.returned,
    flag: ReviewStatus.flagged,
  };

  const visitStatusMap = {
    confirm: VisitStatus.confirmed,
    return: VisitStatus.returned,
    flag: VisitStatus.pending_review,
  };

  const updated = await prisma.triageResult.update({
    where: { triageId },
    data: {
      reviewStatus: reviewStatusMap[action],
      reviewComment: reviewComment || null,
    },
  });

  await prisma.visit.update({
    where: { visitId: triage.visitId },
    data: {
      status: visitStatusMap[action],
      reviewerId: doctorUserId,
      reviewTime: new Date(),
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: doctorUserId,
      action: action === "confirm" ? "review_confirm" : "review_return",
      targetType: "triage_result",
      targetId: triageId,
      detail: { action, reviewComment },
    },
  });

  return {
    triageId,
    reviewStatus: updated.reviewStatus,
    message: `审核操作${action}已完成`,
  };
}

export async function getTriageByVisitId(visitId: string, userId: string, role: string) {
  const triage = await prisma.triageResult.findUnique({
    where: { visitId },
  });
  if (!triage) {
    throw new AppError("分诊结果不存在", 404);
  }
  if (role === "patient") {
    throw new AppError("患者无权查看风险评定", 403);
  }
  return triage;
}