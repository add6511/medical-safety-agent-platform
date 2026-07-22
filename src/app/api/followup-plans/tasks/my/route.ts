import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getMyFollowupTasks } from "@/Services/FollowupService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const result = await getMyFollowupTasks(auth.userId);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["patient"])(request, { params: Promise.resolve({}) });
}