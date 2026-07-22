import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { createFollowupPlan, getFollowupPlanList } from "@/Services/FollowupService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function POST(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const body = await req.json();

      if (!body.patientId || !body.visitId || !body.frequency || !body.startDate || !body.endDate) {
        return errorResponse("缺少必填参数", 422);
      }

      const result = await createFollowupPlan(auth.userId, body);
      return successResponse(result, 201);
    } catch (error) {
      return handleError(error);
    }
  }, ["follower"])(request, { params: Promise.resolve({}) });
}

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { searchParams } = new URL(req.url);
      const query = {
        status: searchParams.get("status") || undefined,
        page: searchParams.get("page") ? parseInt(searchParams.get("page")!) : undefined,
        pageSize: searchParams.get("pageSize") ? parseInt(searchParams.get("pageSize")!) : undefined,
      };
      const result = await getFollowupPlanList(auth.userId, auth.role, query);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["follower", "patient", "admin"])(request, { params: Promise.resolve({}) });
}