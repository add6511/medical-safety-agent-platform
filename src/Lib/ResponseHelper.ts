import { NextResponse } from "next/server";

export function successResponse(data: unknown, statusCode: number = 200) {
  return NextResponse.json(
    { success: true, data },
    { status: statusCode }
  );
}

export function errorResponse(
  message: string,
  statusCode: number = 400,
  errors?: unknown
) {
  const body: Record<string, unknown> = { success: false, message };
  if (errors) body.errors = errors;
  return NextResponse.json(body, { status: statusCode });
}