import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { updateRule } from "@/Services/AdminService";
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
      const body = await req.json();
      const result = await updateRule(auth.userId, ruleId, body);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params });
}