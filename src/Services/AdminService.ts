import { prisma } from "@/Lib/Prisma";
import { AppError } from "@/Middleware/ErrorHandler";
import { validatePagination } from "@/Lib/Validator";
import { desensitizeRealName, desensitizePhone } from "@/Lib/Desensitizer";

export async function createRule(
  adminUserId: string,
  data: { ruleType: string; name: string; condition: string; description: string }
) {
  const rule = await prisma.ruleEngineRule.create({
    data: {
      ruleType: data.ruleType as never,
      name: data.name,
      condition: data.condition,
      description: data.description,
      version: "v1",
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "rule_create",
      targetType: "rule_engine_rule",
      targetId: rule.ruleId,
      detail: { name: data.name, version: rule.version },
    },
  });

  return { ruleId: rule.ruleId, version: rule.version };
}

export async function updateRule(
  adminUserId: string,
  ruleId: string,
  data: { name?: string; condition?: string; description?: string }
) {
  const current = await prisma.ruleEngineRule.findUnique({ where: { ruleId } });
  if (!current) {
    throw new AppError("规则不存在", 404);
  }

  const versionNum = parseInt(current.version.replace("v", "")) + 1;

  const updated = await prisma.ruleEngineRule.update({
    where: { ruleId },
    data: {
      name: data.name ?? current.name,
      condition: data.condition ?? current.condition,
      description: data.description ?? current.description,
      version: `v${versionNum}`,
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "rule_update",
      targetType: "rule_engine_rule",
      targetId: ruleId,
      detail: { version: updated.version },
    },
  });

  return updated;
}

export async function deactivateRule(adminUserId: string, ruleId: string) {
  const rule = await prisma.ruleEngineRule.findUnique({ where: { ruleId } });
  if (!rule) {
    throw new AppError("规则不存在", 404);
  }

  await prisma.ruleEngineRule.update({
    where: { ruleId },
    data: { status: "deprecated" },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "rule_update",
      targetType: "rule_engine_rule",
      targetId: ruleId,
      detail: { action: "deactivate" },
    },
  });

  return { ruleId, status: "deprecated" };
}

export async function updateModelConfig(
  adminUserId: string,
  data: { modelVersion: string; promptVersion: string; knowledgeBaseVersion: string }
) {
  await prisma.modelConfig.updateMany({
    where: { isActive: true },
    data: { isActive: false },
  });

  const config = await prisma.modelConfig.create({
    data: {
      modelVersion: data.modelVersion,
      promptVersion: data.promptVersion,
      knowledgeBaseVersion: data.knowledgeBaseVersion,
      isActive: true,
      updatedBy: adminUserId,
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "model_switch",
      targetType: "model_config",
      targetId: config.configId,
      detail: {
        modelVersion: data.modelVersion,
        promptVersion: data.promptVersion,
      },
    },
  });

  return {
    modelVersion: config.modelVersion,
    promptVersion: config.promptVersion,
    knowledgeBaseVersion: config.knowledgeBaseVersion,
    updateTime: config.updateTime.toISOString(),
  };
}

export async function changeUserRole(
  adminUserId: string,
  targetUserId: string,
  newRole: string
) {
  const user = await prisma.user.findUnique({ where: { userId: targetUserId } });
  if (!user) {
    throw new AppError("目标用户不存在", 404);
  }

  await prisma.user.update({
    where: { userId: targetUserId },
    data: { role: newRole as never },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "permission_change",
      targetType: "user",
      targetId: targetUserId,
      detail: { oldRole: user.role, newRole },
    },
  });

  return { userId: targetUserId, newRole };
}

export async function getUserList(query: {
  role?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}) {
  const { page, pageSize } = validatePagination(query.page, query.pageSize);

  const where: Record<string, unknown> = {};
  if (query.role) where.role = query.role;
  if (query.status) where.status = query.status;

  const [total, items] = await Promise.all([
    prisma.user.count({ where }),
    prisma.user.findMany({
      where,
      orderBy: { createTime: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
      select: {
        userId: true,
        username: true,
        role: true,
        realName: true,
        phone: true,
        status: true,
        createTime: true,
      },
    }),
  ]);

  return {
    total,
    page,
    pageSize,
    items: items.map((u) => ({
      ...u,
      realName: desensitizeRealName(u.realName),
      phone: desensitizePhone(u.phone),
    })),
  };
}