import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { terminateFollowupPlan } from "@/Services/FollowupService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ planId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { planId } = await params;
      const body = await req.json();

      if (!body.terminateReason) {
        return errorResponse("终止原因必填", 422);
      }

      const result = await terminateFollowupPlan(planId, auth.userId, body.terminateReason);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["follower"])(request, { params });
}