import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { resubmitVisit } from "@/Services/VisitService";
import { processVisitSubmission } from "@/Services/VisitProcessingService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ visitId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      if (auth.role !== "patient") {
        return errorResponse("仅患者可重新提交", 403);
      }

      const { visitId } = await params;
      const body = await req.json();
      const result = await resubmitVisit(visitId, auth.userId, body);

      processVisitSubmission(visitId).catch(() => {});

      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["patient"])(request, { params });
}