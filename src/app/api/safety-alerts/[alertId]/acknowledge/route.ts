import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { acknowledgeAlert } from "@/Services/AlertService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ alertId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { alertId } = await params;
      const result = await acknowledgeAlert(alertId, auth.userId);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params });
}