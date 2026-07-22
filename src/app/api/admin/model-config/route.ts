import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { updateModelConfig } from "@/Services/AdminService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const body = await req.json();

      if (!body.modelVersion || !body.promptVersion || !body.knowledgeBaseVersion) {
        return errorResponse("缺少必填参数", 422);
      }

      const result = await updateModelConfig(auth.userId, body);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params: Promise.resolve({}) });
}