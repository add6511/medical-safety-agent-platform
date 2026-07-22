import { NextRequest } from "next/server";
import { prisma } from "@/Lib/Prisma";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { TaskStatus } from "@prisma/client";

export async function POST(request: NextRequest) {
  try {
    const cronSecret = request.headers.get("X-Cron-Secret");
    if (cronSecret !== process.env.CRON_SECRET) {
      return errorResponse("未授权访问", 401);
    }

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(23, 59, 59, 999);

    const tasks = await prisma.followupTask.findMany({
      where: {
        plannedDate: { lte: tomorrow },
        status: TaskStatus.pending,
      },
    });

    const result = await prisma.followupTask.updateMany({
      where: {
        plannedDate: { lte: tomorrow },
        status: TaskStatus.pending,
      },
      data: { status: TaskStatus.reminded },
    });

    return successResponse({ remindedCount: result.count, taskIds: tasks.map((t) => t.taskId) });
  } catch (error) {
    return errorResponse("随访提醒任务执行失败", 500);
  }
}