import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { getVisitDetail } from "@/Services/VisitService";
import { successResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ visitId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { visitId } = await params;
      const result = await getVisitDetail(visitId, auth.userId, auth.role);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  })(request, { params });
}