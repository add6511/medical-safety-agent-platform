import { NextRequest } from "next/server";
import { prisma } from "@/Lib/Prisma";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { VisitStatus, AlertSeverity } from "@prisma/client";

export async function POST(request: NextRequest) {
  try {
    const cronSecret = request.headers.get("X-Cron-Secret");
    if (cronSecret !== process.env.CRON_SECRET) {
      return errorResponse("未授权访问", 401);
    }

    const twoHoursAgo = new Date();
    twoHoursAgo.setHours(twoHoursAgo.getHours() - 2);

    const overdueVisits = await prisma.visit.findMany({
      where: {
        status: VisitStatus.pending_review,
        riskLevel: "high",
        submitTime: { lt: twoHoursAgo },
      },
    });

    for (const visit of overdueVisits) {
      await prisma.safetyAlert.create({
        data: {
          alertType: "unauthorized_diagnosis",
          severity: AlertSeverity.warning,
          sourceType: "system_check",
          sourceId: visit.visitId,
          detail: { message: "高风险病历审核超时", submitTime: visit.submitTime },
        },
      });
    }

    return successResponse({ overdueCount: overdueVisits.length });
  } catch (error) {
    return errorResponse("审核超时检测任务执行失败", 500);
  }
}