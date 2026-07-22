import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { prisma } from "@/Lib/Prisma";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ visitId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      if (auth.role !== "doctor" && auth.role !== "admin") {
        return errorResponse("权限不足", 403);
      }

      const { visitId } = await params;
      const logs = await prisma.auditLog.findMany({
        where: { targetType: "visit", targetId: visitId },
        orderBy: { createTime: "desc" },
      });

      return successResponse(logs);
    } catch (error) {
      return handleError(error);
    }
  }, ["doctor", "admin"])(request, { params });
}