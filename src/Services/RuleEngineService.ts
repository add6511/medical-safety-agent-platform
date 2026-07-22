import { prisma } from "@/Lib/Prisma";
import { VisitStatus, RiskLevel } from "@prisma/client";
import { AppError } from "@/Middleware/ErrorHandler";

export async function checkRedFlagSymptoms(
  symptoms: Array<{ symptomName: string; isRedFlag: boolean }>
) {
  const rules = await prisma.ruleEngineRule.findMany({
    where: { ruleType: "red_flag", status: "active" },
  });

  const results: Array<{
    symptomName: string;
    matched: boolean;
    ruleName?: string;
  }> = [];

  for (const symptom of symptoms) {
    const matchedRule = rules.find((rule) => {
      try {
        const condition = JSON.parse(rule.condition);
        return condition.symptomNames?.includes(symptom.symptomName);
      } catch {
        return symptom.symptomName.includes(rule.condition);
      }
    });

    results.push({
      symptomName: symptom.symptomName,
      matched: !!matchedRule,
      ruleName: matchedRule?.name,
    });
  }

  return results;
}

export async function checkContraindications(
  medicalHistory: string,
  _medications?: string
) {
  const rules = await prisma.ruleEngineRule.findMany({
    where: { ruleType: "contraindication", status: "active" },
  });

  const results: Array<{ ruleName: string; matched: boolean }> = [];

  for (const rule of rules) {
    try {
      const condition = JSON.parse(rule.condition);
      const matched = condition.keywords?.some((kw: string) =>
        medicalHistory.includes(kw)
      );
      results.push({ ruleName: rule.name, matched: !!matched });
    } catch {
      const matched = medicalHistory.includes(rule.condition);
      results.push({ ruleName: rule.name, matched });
    }
  }

  return results;
}

export function assessRiskLevel(
  redFlagResults: Array<{ matched: boolean }>,
  contraindicationResults: Array<{ matched: boolean }>
): RiskLevel {
  const hasRedFlag = redFlagResults.some((r) => r.matched);
  const hasContraindication = contraindicationResults.some(
    (r) => r.matched
  );

  if (hasRedFlag) return RiskLevel.high;
  if (hasContraindication) return RiskLevel.medium;
  return RiskLevel.low;
}

export async function getCurrentRuleVersion() {
  const rules = await prisma.ruleEngineRule.findMany({
    where: { status: "active" },
    orderBy: { version: "desc" },
  });
  return rules.map((r) => `${r.name}@${r.version}`).join(",");
}

export async function executePreScreening(visitId: string) {
  const visit = await prisma.visit.findUnique({
    where: { visitId },
    include: { symptoms: true, patient: true },
  });
  if (!visit) {
    throw new AppError("就诊记录不存在", 404);
  }

  await prisma.visit.update({
    where: { visitId },
    data: { status: VisitStatus.screening },
  });

  const redFlagResults = await checkRedFlagSymptoms(visit.symptoms);
  const contraindicationResults = await checkContraindications(
    visit.patient.medicalHistorySummary || ""
  );
  const riskLevel = assessRiskLevel(redFlagResults, contraindicationResults);
  const ruleVersion = await getCurrentRuleVersion();

  for (const result of redFlagResults) {
    if (result.matched) {
      await prisma.symptom.updateMany({
        where: { visitId, symptomName: result.symptomName },
        data: { isRedFlag: true },
      });
    }
  }

  await prisma.visit.update({
    where: { visitId },
    data: { riskLevel, status: VisitStatus.ai_reviewing },
  });

  return {
    redFlagResults,
    contraindicationResults,
    riskLevel,
    ruleVersion,
  };
}