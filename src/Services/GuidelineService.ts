import { prisma } from "@/Lib/Prisma";
import { AppError } from "@/Middleware/ErrorHandler";
import { validatePagination } from "@/Lib/Validator";

const GUIDELINE_SERVICE_URL =
  process.env.GUIDELINE_SERVICE_URL || "http://localhost:8001/api";

export async function searchGuidelines(
  keyword?: string,
  category?: string,
  page?: number,
  pageSize?: number
) {
  const { page: p, pageSize: ps } = validatePagination(page, pageSize);

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    const params = new URLSearchParams();
    if (keyword) params.set("keyword", keyword);
    if (category) params.set("category", category);
    params.set("page", p.toString());
    params.set("pageSize", ps.toString());

    const response = await fetch(
      `${GUIDELINE_SERVICE_URL}/search?${params.toString()}`,
      { signal: controller.signal }
    );

    clearTimeout(timeout);

    if (!response.ok) {
      return { total: 0, items: [], message: "指南服务暂时不可用" };
    }
    return await response.json();
  } catch {
    return { total: 0, items: [], message: "指南服务暂时不可用" };
  }
}

export async function getGuidelineDetail(guidelineId: string) {
  const guideline = await prisma.medicalGuideline.findUnique({
    where: { guidelineId },
  });
  if (!guideline) {
    throw new AppError("指南不存在", 404);
  }
  return guideline;
}

export async function createGuideline(
  adminUserId: string,
  data: {
    title: string;
    sourceOrg: string;
    publishDate: string;
    category: string;
    content: string;
  }
) {
  if (!data.sourceOrg) {
    throw new AppError("来源机构必填", 422);
  }

  const guideline = await prisma.medicalGuideline.create({
    data: {
      title: data.title,
      sourceOrg: data.sourceOrg,
      publishDate: new Date(data.publishDate),
      category: data.category,
      content: data.content,
      version: "v1",
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "guideline_create",
      targetType: "medical_guideline",
      targetId: guideline.guidelineId,
      detail: { title: data.title },
    },
  });

  return { guidelineId: guideline.guidelineId };
}

export async function updateGuideline(
  adminUserId: string,
  guidelineId: string,
  data: {
    title?: string;
    sourceOrg?: string;
    publishDate?: string;
    category?: string;
    content?: string;
  }
) {
  const current = await prisma.medicalGuideline.findUnique({
    where: { guidelineId },
  });
  if (!current) {
    throw new AppError("指南不存在", 404);
  }

  const versionNum = parseInt(current.version.replace("v", "")) + 1;

  const updated = await prisma.medicalGuideline.update({
    where: { guidelineId },
    data: {
      title: data.title ?? current.title,
      sourceOrg: data.sourceOrg ?? current.sourceOrg,
      publishDate: data.publishDate
        ? new Date(data.publishDate)
        : current.publishDate,
      category: data.category ?? current.category,
      content: data.content ?? current.content,
      version: `v${versionNum}`,
    },
  });

  await prisma.auditLog.create({
    data: {
      operatorId: adminUserId,
      action: "guideline_update",
      targetType: "medical_guideline",
      targetId: guidelineId,
      detail: { version: updated.version },
    },
  });

  return updated;
}