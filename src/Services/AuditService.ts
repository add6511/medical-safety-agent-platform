import { prisma } from "@/Lib/Prisma";
import { Prisma } from "@prisma/client";
import { validatePagination } from "@/Lib/Validator";

export async function createAuditLog(
  operatorId: string,
  action: string,
  targetType: string,
  targetId: string,
  detail: Record<string, unknown>
) {
  const log = await prisma.auditLog.create({
    data: {
      operatorId,
      action: action as never,
      targetType,
      targetId,
      detail: detail as Prisma.InputJsonValue,
    },
  });
  return { logId: log.logId };
}

export async function getAuditLogList(query: {
  operatorId?: string;
  action?: string;
  targetType?: string;
  startTime?: string;
  endTime?: string;
  page?: number;
  pageSize?: number;
}) {
  const { page, pageSize } = validatePagination(query.page, query.pageSize);

  const where: Record<string, unknown> = {};
  if (query.operatorId) where.operatorId = query.operatorId;
  if (query.action) where.action = query.action;
  if (query.targetType) where.targetType = query.targetType;
  if (query.startTime || query.endTime) {
    const createTime: Record<string, Date> = {};
    if (query.startTime) createTime.gte = new Date(query.startTime);
    if (query.endTime) createTime.lte = new Date(query.endTime);
    where.createTime = createTime;
  }

  const [total, items] = await Promise.all([
    prisma.auditLog.count({ where }),
    prisma.auditLog.findMany({
      where,
      orderBy: { createTime: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
    }),
  ]);

  return { total, page, pageSize, items };
}

export async function exportAuditLogs(query: {
  operatorId?: string;
  action?: string;
  targetType?: string;
  startTime?: string;
  endTime?: string;
}) {
  const where: Record<string, unknown> = {};
  if (query.operatorId) where.operatorId = query.operatorId;
  if (query.action) where.action = query.action;
  if (query.targetType) where.targetType = query.targetType;

  const logs = await prisma.auditLog.findMany({
    where,
    orderBy: { createTime: "desc" },
    take: 10000,
  });

  const header = "log_id,operator_id,action,target_type,target_id,create_time\n";
  const rows = logs
    .map(
      (l) =>
        `${l.logId},${l.operatorId},${l.action},${l.targetType},${l.targetId},${l.createTime.toISOString()}`
    )
    .join("\n");

  return header + rows;
}