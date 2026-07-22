import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getGuidelineDetail, updateGuideline } from "@/Services/GuidelineService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ guidelineId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { guidelineId } = await params;
      const result = await getGuidelineDetail(guidelineId);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["doctor", "follower", "admin"])(request, { params });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ guidelineId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { guidelineId } = await params;
      const body = await req.json();
      const result = await updateGuideline(auth.userId, guidelineId, body);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params });
}