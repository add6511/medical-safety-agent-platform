import { NextResponse } from "next/server";
import { prisma } from "@/Lib/Prisma";

export async function GET() {
  const result: {
    status: "healthy" | "degraded" | "unhealthy";
    components: {
      database: "up" | "down";
      aiService: "up" | "down" | "unknown";
      guidelineService: "up" | "down" | "unknown";
    };
    timestamp: string;
  } = {
    status: "healthy",
    components: {
      database: "up",
      aiService: "unknown",
      guidelineService: "unknown",
    },
    timestamp: new Date().toISOString(),
  };

  try {
    await prisma.$queryRaw`SELECT 1`;
    result.components.database = "up";
  } catch {
    result.components.database = "down";
    result.status = "unhealthy";
  }

  try {
    const aiUrl = process.env.AI_SERVICE_URL || "http://localhost:8000/api";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const aiRes = await fetch(`${aiUrl}/health`, { signal: controller.signal });
    clearTimeout(timeout);
    result.components.aiService = aiRes.ok ? "up" : "down";
  } catch {
    result.components.aiService = "unknown";
  }

  try {
    const guidelineUrl = process.env.GUIDELINE_SERVICE_URL || "http://localhost:8001/api";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const guidelineRes = await fetch(`${guidelineUrl}/health`, { signal: controller.signal });
    clearTimeout(timeout);
    result.components.guidelineService = guidelineRes.ok ? "up" : "down";
  } catch {
    result.components.guidelineService = "unknown";
  }

  if (result.components.database === "down") {
    result.status = "unhealthy";
  } else if (
    result.components.aiService === "down" ||
    result.components.guidelineService === "down"
  ) {
    result.status = "degraded";
  }

  return NextResponse.json(result);
}