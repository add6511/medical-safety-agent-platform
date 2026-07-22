import { NextRequest } from "next/server";
import { withAuth } from "@/Middleware/AuthMiddleware";
import { changeUserRole } from "@/Services/AdminService";
import { successResponse, errorResponse } from "@/Lib/ResponseHelper";
import { handleError } from "@/Middleware/ErrorHandler";

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  return withAuth(async (req) => {
    try {
      const { auth } = req as NextRequest & { auth: { userId: string; role: string } };
      const { userId } = await params;
      const body = await req.json();

      if (!body.newRole || !["patient", "doctor", "follower", "admin"].includes(body.newRole)) {
        return errorResponse("角色参数无效", 422);
      }

      const result = await changeUserRole(auth.userId, userId, body.newRole);
      return successResponse(result);
    } catch (error) {
      return handleError(error);
    }
  }, ["admin"])(request, { params });
}