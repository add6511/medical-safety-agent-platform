import { prisma } from "@/Lib/Prisma";
import { AppError } from "@/Middleware/ErrorHandler";
import { desensitizeRealName, desensitizePhone } from "@/Lib/Desensitizer";
import { validatePagination } from "@/Lib/Validator";
import { VisitStatus, RiskLevel } from "@prisma/client";

export async function createVisit(
  patientUserId: string,
  data: {
    chiefComplaint: string;
    caseTag: string;
    ageGroup: string;
    gender: string;
    medicalHistorySummary?: string;
    symptoms: Array<{
      symptomName: string;
      bodyPart?: string;
      duration?: string;
      severity?: string;
      originalText: string;
    }>;
  }
) {
  if (data.caseTag !== "synthetic") {
    throw new AppError("仅允许提交合成病例（caseTag必须为synthetic）", 422);
  }
  if (!data.chiefComplaint || data.chiefComplaint.length > 500) {
    throw new AppError("主诉必填且最大500字符", 422);
  }
  if (!data.symptoms || data.symptoms.length < 1) {
    throw new AppError("至少需要1个症状", 422);
  }

  const patient = await prisma.simulatedPatient.findUnique({
    where: { userId: patientUserId },
  });
  if (!patient) {
    throw new AppError("患者记录不存在", 404);
  }

  const visit = await prisma.visit.create({
    data: {
      patientId: patient.patientId,
      status: VisitStatus.submitted,
      chiefComplaint: data.chiefComplaint,
      riskLevel: RiskLevel.pending,
      submitTime: new Date(),
      symptoms: {
        create: data.symptoms.map((s) => ({
          symptomName: s.symptomName,
          bodyPart: s.bodyPart,
          duration: s.duration,
          severity: s.severity as never,
          isRedFlag: false,
          originalText: s.originalText,
        })),
      },
    },
  });

  return { visitId: visit.visitId, status: visit.status };
}

export async function getVisitList(
  userId: string,
  role: string,
  query: { status?: string; riskLevel?: string; page?: number; pageSize?: number }
) {
  const { page, pageSize } = validatePagination(query.page, query.pageSize);

  const where: Record<string, unknown> = {};

  if (role === "patient") {
    const patient = await prisma.simulatedPatient.findUnique({
      where: { userId },
    });
    if (patient) where.patientId = patient.patientId;
  }

  if (query.status) where.status = query.status;
  if (query.riskLevel) where.riskLevel = query.riskLevel;

  const [total, items] = await Promise.all([
    prisma.visit.count({ where }),
    prisma.visit.findMany({
      where,
      orderBy: { riskLevel: "desc" },
      skip: (page - 1) * pageSize,
      take: pageSize,
      include: { symptoms: true },
    }),
  ]);

  return {
    total,
    page,
    pageSize,
    items: items.map((v) => ({
      visitId: v.visitId,
      patientId: v.patientId,
      chiefComplaint: v.chiefComplaint,
      riskLevel: v.riskLevel,
      status: v.status,
      submitTime: v.submitTime?.toISOString(),
      reviewerId: v.reviewerId,
    })),
  };
}

export async function getVisitDetail(
  visitId: string,
  userId: string,
  role: string
) {
  const visit = await prisma.visit.findUnique({
    where: { visitId },
    include: { symptoms: true, triageResult: true },
  });
  if (!visit) {
    throw new AppError("就诊记录不存在", 404);
  }

  if (role === "patient") {
    const patient = await prisma.simulatedPatient.findUnique({
      where: { userId },
    });
    if (!patient || patient.patientId !== visit.patientId) {
      throw new AppError("无权访问该记录", 403);
    }
  }

  const result: Record<string, unknown> = {
    visitId: visit.visitId,
    patientId: visit.patientId,
    status: visit.status,
    chiefComplaint: visit.chiefComplaint,
    riskLevel: visit.riskLevel,
    submitTime: visit.submitTime?.toISOString(),
    reviewTime: visit.reviewTime?.toISOString(),
    reviewerId: visit.reviewerId,
    symptoms: visit.symptoms.map((s) => ({
      symptomId: s.symptomId,
      symptomName: s.symptomName,
      bodyPart: s.bodyPart,
      duration: s.duration,
      severity: s.severity,
      isRedFlag: s.isRedFlag,
      originalText: s.originalText,
    })),
  };

  if (role !== "patient" && visit.triageResult) {
    result.triageResult = {
      triageId: visit.triageResult.triageId,
      riskLevel: visit.triageResult.riskLevel,
      riskEvidence: visit.triageResult.riskEvidence,
      ruleVersion: visit.triageResult.ruleVersion,
      aiOutput: visit.triageResult.aiOutput,
      safetyCheckPassed: visit.triageResult.safetyCheckPassed,
      reviewStatus: visit.triageResult.reviewStatus,
      reviewComment: visit.triageResult.reviewComment,
    };
  }

  return result;
}

export async function resubmitVisit(
  visitId: string,
  patientUserId: string,
  data: {
    chiefComplaint: string;
    symptoms: Array<{
      symptomName: string;
      bodyPart?: string;
      duration?: string;
      severity?: string;
      originalText: string;
    }>;
  }
) {
  const visit = await prisma.visit.findUnique({ where: { visitId } });
  if (!visit) {
    throw new AppError("就诊记录不存在", 404);
  }
  if (visit.status !== VisitStatus.returned) {
    throw new AppError("仅退回状态的记录可重新提交", 409);
  }

  const patient = await prisma.simulatedPatient.findUnique({
    where: { userId: patientUserId },
  });
  if (!patient || patient.patientId !== visit.patientId) {
    throw new AppError("无权操作该记录", 403);
  }

  await prisma.symptom.deleteMany({ where: { visitId } });

  const updated = await prisma.visit.update({
    where: { visitId },
    data: {
      chiefComplaint: data.chiefComplaint,
      status: VisitStatus.submitted,
      submitTime: new Date(),
      symptoms: {
        create: data.symptoms.map((s) => ({
          symptomName: s.symptomName,
          bodyPart: s.bodyPart,
          duration: s.duration,
          severity: s.severity as never,
          isRedFlag: false,
          originalText: s.originalText,
        })),
      },
    },
  });

  return { visitId: updated.visitId, status: updated.status };
}