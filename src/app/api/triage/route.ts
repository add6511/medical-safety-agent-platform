import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getTriageByVisitId } from "@/Services/VisitProcessingService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      if (auth.role === "patient") {
        return errorResponse("患者无权查看风险评定", 403);
      }

      const { searchParams } = new URL(req.url);
      const visitId = searchParams.get("visitId");
      if (!visitId) {
        return errorResponse("visitId参数必填", 422);
      }

      const result = await getTriageByVisitId(visitId, auth.userId, auth.role);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["doctor", "admin"])(request, { params: Promise.resolve({}) });
}