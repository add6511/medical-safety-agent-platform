import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getAuditLogList } from "@/Services/AuditService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { searchParams } = new URL(req.url);
      const query = {
        operatorId: searchParams.get("operatorId") || undefined,
        action: searchParams.get("action") || undefined,
        targetType: searchParams.get("targetType") || undefined,
        startTime: searchParams.get("startTime") || undefined,
        endTime: searchParams.get("endTime") || undefined,
        page: searchParams.get("page") ? parseInt(searchParams.get("page")!) : undefined,
        pageSize: searchParams.get("pageSize") ? parseInt(searchParams.get("pageSize")!) : undefined,
      };
      const result = await getAuditLogList(query);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params: Promise.resolve({}) });
}