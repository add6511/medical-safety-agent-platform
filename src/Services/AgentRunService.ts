import { prisma } from "@/Lib/Prisma";
import { Prisma } from "@prisma/client";

export async function createAgentRun(
  visitId: string,
  modelVersion: string,
  promptVersion: string,
  knowledgeBaseVersion: string,
  inputContent: Record<string, unknown>,
  outputContent: Record<string, unknown>,
  safetyCheckResult: Record<string, unknown>
) {
  const run = await prisma.agentRun.create({
    data: {
      visitId,
      modelVersion,
      promptVersion,
      knowledgeBaseVersion,
      inputContent: inputContent as Prisma.InputJsonValue,
      outputContent: outputContent as Prisma.InputJsonValue,
      safetyCheckResult: safetyCheckResult as Prisma.InputJsonValue,
    },
  });
  return { runId: run.runId };
}

export async function createCitations(
  agentRunId: string,
  citations: Array<{
    guidelineId: string;
    referencedSection: string;
    relevanceScore: number;
  }>
) {
  const result = await prisma.citation.createMany({
    data: citations.map((c) => ({
      agentRunId,
      guidelineId: c.guidelineId,
      referencedSection: c.referencedSection,
      relevanceScore: c.relevanceScore,
    })),
  });
  return { count: result.count };
}
