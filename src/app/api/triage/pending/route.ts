import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getPendingReviewList } from "@/Services/VisitProcessingService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { searchParams } = new URL(req.url);
      const query = {
        page: searchParams.get("page") ? parseInt(searchParams.get("page")!) : undefined,
        pageSize: searchParams.get("pageSize") ? parseInt(searchParams.get("pageSize")!) : undefined,
      };
      const result = await getPendingReviewList(auth.userId, query);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["doctor"])(request, { params: Promise.resolve({}) });
}