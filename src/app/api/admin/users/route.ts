import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getUserList } from "@/Services/AdminService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { searchParams } = new URL(req.url);
      const query = {
        role: searchParams.get("role") || undefined,
        status: searchParams.get("status") || undefined,
        page: searchParams.get("page") ? parseInt(searchParams.get("page")!) : undefined,
        pageSize: searchParams.get("pageSize") ? parseInt(searchParams.get("pageSize")!) : undefined,
      };
      const result = await getUserList(query);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params: Promise.resolve({}) });
}