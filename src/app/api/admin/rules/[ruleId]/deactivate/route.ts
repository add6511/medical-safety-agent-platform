import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { deactivateRule } from "@/Services/AdminService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ ruleId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { ruleId } = await params;
      const result = await deactivateRule(auth.userId, ruleId);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params });
}