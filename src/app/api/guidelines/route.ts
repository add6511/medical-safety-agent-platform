import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { searchGuidelines, createGuideline } from "@/Services/GuidelineService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { searchParams } = new URL(req.url);
      const result = await searchGuidelines(
        searchParams.get("keyword") || undefined,
        searchParams.get("category") || undefined,
        searchParams.get("page") ? parseInt(searchParams.get("page")!) : undefined,
        searchParams.get("pageSize") ? parseInt(searchParams.get("pageSize")!) : undefined
      );
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["doctor", "follower", "admin"])(request, { params: Promise.resolve({}) });
}

export async function POST(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const body = await req.json();

      if (!body.title || !body.sourceOrg || !body.content) {
        return errorResponse("标题、来源机构和内容必填", 422);
      }

      const result = await createGuideline(auth.userId, body);
      return successResponse(result, 201);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params: Promise.resolve({}) });
}