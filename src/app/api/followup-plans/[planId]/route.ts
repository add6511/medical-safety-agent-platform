import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getFollowupPlanDetail } from "@/Services/FollowupService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ planId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { planId } = await params;
      const result = await getFollowupPlanDetail(planId, auth.userId, auth.role);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  })(request, { params });
}