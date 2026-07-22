import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { reviewTriage } from "@/Services/VisitProcessingService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ triageId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { triageId } = await params;
      const body = await req.json();

      if (!body.action || !["confirm", "return", "flag"].includes(body.action)) {
        return errorResponse("审核操作类型无效", 422);
      }

      const result = await reviewTriage(
        triageId,
        auth.userId,
        body.action,
        body.reviewComment
      );
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["doctor"])(request, { params });
}