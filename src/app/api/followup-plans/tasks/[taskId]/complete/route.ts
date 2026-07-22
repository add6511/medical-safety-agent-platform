import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { completeFollowupTask } from "@/Services/FollowupService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ taskId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { taskId } = await params;
      const body = await req.json();

      if (!body.resultNote) {
        return errorResponse("随访结果必填", 422);
      }

      const result = await completeFollowupTask(taskId, auth.userId, body.resultNote);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["follower"])(request, { params });
}