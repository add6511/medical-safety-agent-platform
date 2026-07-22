import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { register } from "@/Services/AuthService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, password, role, realName, phone } = body;

    if (!username || !password || !role || !realName || !phone) {
      return errorResponse("缺少必填参数", 422);
    }

    const result = await register(username, password, role, realName, phone);
    return successResponse(result, 201);
  } catch (error) {
    return handleError(error);
  }
}