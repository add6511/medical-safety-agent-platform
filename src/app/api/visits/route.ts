import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { createVisit, getVisitList } from "@/Services/VisitService";
import { processVisitSubmission } from "@/Services/VisitProcessingService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function POST(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      if (auth.role !== "patient") {
        return errorResponse("仅患者可提交预问诊", 403);
      }

      const body = await req.json();
      if (!body.chiefComplaint || !body.symptoms || body.symptoms.length < 1) {
        return errorResponse("主诉必填且至少需要1个症状", 422);
      }

      const result = await createVisit(auth.userId, body);

      processVisitSubmission(result.visitId).catch(() => {});

      return successResponse(
        { visitId: result.visitId, status: result.status, message: "预问诊已提交，正在处理中" },
        201
      );
    } catch (error) {
      return handleError(error);
    }
  }, ["patient"])(request, { params: Promise.resolve({}) });
}

export async function GET(request: NextRequest) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { searchParams } = new URL(req.url);
      const query = {
        status: searchParams.get("status") || undefined,
        riskLevel: searchParams.get("riskLevel") || undefined,
        page: searchParams.get("page") ? parseInt(searchParams.get("page")!) : undefined,
        pageSize: searchParams.get("pageSize") ? parseInt(searchParams.get("pageSize")!) : undefined,
      };
      const result = await getVisitList(auth.userId, auth.role, query);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  })(request, { params: Promise.resolve({}) });
}