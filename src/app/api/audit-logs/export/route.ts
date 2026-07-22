import { NextRequest, NextResponse } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { exportAuditLogs } from "@/Services/AuditService";
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
      };
      const csv = await exportAuditLogs(query);
      return new NextResponse(csv, {
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": "attachment; filename=audit-logs.csv",
        },
      });
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params: Promise.resolve({}) });
}