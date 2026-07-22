import { prisma } from "@/Lib/Prisma";
import { AlertSeverity } from "@prisma/client";

const DIAGNOSIS_PATTERNS = [
  /诊断为/g,
  /确诊为/g,
  /患有.+病/g,
  /罹患/g,
  /所患疾病为/g,
];

const ATTACK_PATTERNS = [
  /忽略指令/gi,
  /忽略以上/gi,
  /输出系统.?prompt/gi,
  /越狱/gi,
  /jailbreak/gi,
  /ignore previous/gi,
  /disregard.*instructions/gi,
];

const PII_PATTERNS = [
  /[\u4e00-\u9fa5]{2,4}(?=\s*(?:身份证|证件号))/g,
  /\d{17}[\dXx]/g,
  /1[3-9]\d{9}/g,
];

export async function detectUnauthorizedDiagnosis(aiOutput: string) {
  const matches: Array<{ pattern: string; original: string }> = [];

  let processedOutput = aiOutput;
  for (const pattern of DIAGNOSIS_PATTERNS) {
    const match = aiOutput.match(pattern);
    if (match) {
      matches.push({ pattern: pattern.source, original: match[0] });
      processedOutput = processedOutput.replace(
        pattern,
        "建议关注"
      );
    }
  }

  if (matches.length > 0) {
    await prisma.safetyAlert.create({
      data: {
        alertType: "unauthorized_diagnosis",
        severity: AlertSeverity.critical,
        sourceType: "ai_output",
        sourceId: "ai_output",
        detail: { matches },
      },
    });
  }

  return { passed: matches.length === 0, processedOutput, matches };
}

export async function detectPromptAttack(userInput: string) {
  const matches: Array<{ pattern: string; original: string }> = [];

  for (const pattern of ATTACK_PATTERNS) {
    const match = userInput.match(pattern);
    if (match) {
      matches.push({ pattern: pattern.source, original: match[0] });
    }
  }

  if (matches.length > 0) {
    await prisma.safetyAlert.create({
      data: {
        alertType: "prompt_attack",
        severity: AlertSeverity.warning,
        sourceType: "user_input",
        sourceId: "user_input",
        detail: { matches },
      },
    });
  }

  return { passed: matches.length === 0, matches };
}

export async function detectPrivacyLeak(
  aiOutput: string,
  _currentPatientId: string
) {
  const leaks: Array<{ type: string; match: string }> = [];

  for (const pattern of PII_PATTERNS) {
    const match = aiOutput.match(pattern);
    if (match) {
      leaks.push({ type: "PII", match: match[0] });
    }
  }

  if (leaks.length > 0) {
    await prisma.safetyAlert.create({
      data: {
        alertType: "privacy_leak",
        severity: AlertSeverity.critical,
        sourceType: "ai_output",
        sourceId: "ai_output",
        detail: { leaks },
      },
    });
  }

  return { passed: leaks.length === 0, leaks };
}

export async function reviewAIOutput(aiOutput: string, visitId: string) {
  const diagnosisResult = await detectUnauthorizedDiagnosis(aiOutput);
  const privacyResult = await detectPrivacyLeak(aiOutput, visitId);

  if (!privacyResult.passed) {
    return {
      status: "blocked" as const,
      reason: "隐私泄露检测未通过",
      processedOutput: null,
    };
  }

  if (!diagnosisResult.passed) {
    return {
      status: "replaced" as const,
      reason: "越权诊断表述已替换",
      processedOutput: diagnosisResult.processedOutput,
    };
  }

  return {
    status: "passed" as const,
    reason: null,
    processedOutput: aiOutput,
  };
}

export async function aggregateAlerts(alerts: Array<{ alertType: string; sourceId: string }>) {
  const grouped = new Map<string, number>();
  for (const alert of alerts) {
    const key = `${alert.alertType}:${alert.sourceId}`;
    grouped.set(key, (grouped.get(key) || 0) + 1);
  }
  return Array.from(grouped.entries()).map(([key, count]) => ({
    key,
    count,
  }));
}