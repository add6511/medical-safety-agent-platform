import { NextRequest } from "next/server";
import { login } from "@/Services/AuthService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, password } = body;

    if (!username || !password) {
      return errorResponse("缺少用户名或密码", 422);
    }

    const result = await login(username, password);
    return successResponse(result);
  } catch (error) {
    return handleError(error);
  }
}