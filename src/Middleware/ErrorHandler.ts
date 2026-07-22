import { NextResponse } from "next/server";
import { Prisma } from "@prisma/client";
import { errorResponse } from "@/Lib/ResponseHelper";

export function handleError(error: unknown): NextResponse {
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    switch (error.code) {
      case "P2002":
        return errorResponse("资源已存在，违反唯一约束", 409);
      case "P2025":
        return errorResponse("资源未找到", 404);
      default:
        return errorResponse("数据库操作失败", 500);
    }
  }

  if (error instanceof Prisma.PrismaClientValidationError) {
    return errorResponse("请求参数校验失败", 422);
  }

  if (error instanceof AppError) {
    return errorResponse(error.message, error.statusCode);
  }

  console.error("Unhandled error:", error);
  return errorResponse("服务器内部错误", 500);
}

export class AppError extends Error {
  statusCode: number;

  constructor(message: string, statusCode: number = 400) {
    super(message);
    this.statusCode = statusCode;
    this.name = "AppError";
  }
}