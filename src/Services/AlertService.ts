import { prisma } from "@/Lib/Prisma";
import { Prisma } from "@prisma/client";
import { validatePagination } from "@/Lib/Validator";

export async function createSafetyAlert(
  alertType: string,
  severity: string,
  sourceType: string,
  sourceId: string,
  detail: Record<string, unknown>
) {
  const alert = await prisma.safetyAlert.create({
    data: {
      alertType: alertType as never,
      severity: severity as never,
      sourceType: sourceType as never,
      sourceId,
      detail: detail as Prisma.InputJsonValue,
    },
  });
  return { alertId: alert.alertId };
}

export async function getSafetyAlertList(query: {
  alertType?: string;
  severity?: string;
  isResolved?: boolean;
  page?: number;
  pageSize?: number;
}) {
  const { page, pageSize } = validatePagination(query.page, query.pageSize);

  const where: Record<string, unknown> = {};
  if (query.alertType) where.alertType = query.alertType;
  if (query.severity) where.severity = query.severity;
  if (query.isResolved !== undefined) where.isResolved = query.isResolved;

  const [total, items] = await Promise.all([
    prisma.safetyAlert.count({ where }),
    prisma.safetyAlert.findMany({
      where,
      orderBy: { createTime: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
    }),
  ]);

  return { total, page, pageSize, items };
}

export async function acknowledgeAlert(alertId: string, adminUserId: string) {
  const alert = await prisma.safetyAlert.findUnique({ where: { alertId } });
  if (!alert) {
    throw new Error("告警不存在");
  }

  await prisma.safetyAlert.update({
    where: { alertId },
    data: { isResolved: true },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "alert_acknowledge",
      targetType: "safety_alert",
      targetId: alertId,
      detail: { alertType: alert.alertType } as Prisma.InputJsonValue,
    },
  });

  return { alertId, isResolved: true };
}
