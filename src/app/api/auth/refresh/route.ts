import { NextRequest } from "next/server";
import { refreshToken } from "@/Services/AuthService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("Authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return errorResponse("未提供认证令牌", 401);
    }

    const token = authHeader.substring(7);
    const result = await refreshToken(token);
    return successResponse(result);
  } catch (error) {
    return handleError(error);
  }
}
