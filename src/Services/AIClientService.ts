import { prisma } from "@/Lib/Prisma";

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000/api";
const AI_TIMEOUT = 30000;

export async function structureSymptoms(rawText: string) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), AI_TIMEOUT);

    const response = await fetch(`${AI_SERVICE_URL}/structure-symptoms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: rawText }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function riskReview(
  structuredData: unknown,
  preScreenResult: unknown
) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), AI_TIMEOUT);

    const response = await fetch(`${AI_SERVICE_URL}/risk-review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ structuredData, preScreenResult }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function getCurrentModelConfig() {
  const config = await prisma.modelConfig.findFirst({
    where: { isActive: true },
  });
  return config
    ? {
        modelVersion: config.modelVersion,
        promptVersion: config.promptVersion,
        knowledgeBaseVersion: config.knowledgeBaseVersion,
      }
    : null;
}