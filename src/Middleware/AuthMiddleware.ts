import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/Lib/JwtHelper";
import { errorResponse } from "@/Lib/ResponseHelper";

type UserRole = "patient" | "doctor" | "follower" | "admin";

const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  patient: [
    "visits:write",
    "visits:read_own",
    "followup:read_own",
    "tasks:read_own",
  ],
  doctor: [
    "visits:read",
    "triage:read",
    "triage:write",
    "guidelines:read",
  ],
  follower: [
    "followup:write",
    "followup:read",
    "guidelines:read",
    "tasks:write",
  ],
  admin: [
    "visits:read",
    "triage:read",
    "guidelines:write",
    "guidelines:read",
    "followup:read",
    "alerts:read",
    "alerts:write",
    "audit:read",
    "admin:write",
    "admin:read",
  ],
};

export interface AuthContext {
  userId: string;
  role: UserRole;
}

type HandlerFunction = (
  request: NextRequest,
  context: { params: Promise<Record<string, string>> } & Record<string, unknown>
) => Promise<NextResponse> | NextResponse;

export function withAuth(
  handler: HandlerFunction,
  allowedRoles?: UserRole[]
): HandlerFunction {
  return async (request, context) => {
    const authHeader = request.headers.get("Authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return errorResponse("未提供认证令牌", 401);
    }

    const token = authHeader.substring(7);
    const payload = verifyToken(token);
    if (!payload) {
      return errorResponse("认证令牌无效或已过期", 401);
    }

    if (allowedRoles && !allowedRoles.includes(payload.role as UserRole)) {
      return errorResponse("权限不足", 403);
    }

    const authContext: AuthContext = {
      userId: payload.userId,
      role: payload.role as UserRole,
    };

    (request as NextRequest & { auth: AuthContext }).auth = authContext;

    return handler(request, context);
  };
}

export function hasPermission(role: UserRole, permission: string): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}