import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { createRule, updateRule, deactivateRule } from "@/Services/AdminService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function POST(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const body = await req.json();

      if (!body.ruleType || !body.name || !body.condition || !body.description) {
        return errorResponse("缺少必填参数", 422);
      }

      const result = await createRule(auth.userId, body);
      return successResponse(result, 201);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params: Promise.resolve({}) });
}