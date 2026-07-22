import { prisma } from "@/Lib/Prisma";
import { generateToken } from "@/Lib/JwtHelper";
import { validateUsername, validatePhone, validatePassword } from "@/Lib/Validator";
import bcrypt from "bcryptjs";
import { AppError } from "@/Middleware/ErrorHandler";

export async function register(
  username: string,
  password: string,
  role: string,
  realName: string,
  phone: string
) {
  if (!validateUsername(username)) {
    throw new AppError("用户名格式不正确，需3-50位字母数字下划线", 422);
  }
  if (!validatePassword(password)) {
    throw new AppError("密码长度需8-64位", 422);
  }
  if (!validatePhone(phone)) {
    throw new AppError("手机号格式不正确", 422);
  }
  if (role !== "patient") {
    throw new AppError("注册仅允许患者模拟用户角色", 422);
  }

  const existing = await prisma.user.findUnique({ where: { username } });
  if (existing) {
    throw new AppError("用户名已被占用", 409);
  }

  const passwordHash = await bcrypt.hash(password, 10);

  const user = await prisma.user.create({
    data: { username, passwordHash, role, realName, phone },
  });

  await prisma.simulatedPatient.create({
    data: {
      userId: user.userId,
      caseTag: "synthetic",
      ageGroup: "middle",
      gender: "other",
    },
  });

  const token = generateToken(user.userId, user.role);

  return { userId: user.userId, token, role: user.role };
}

export async function login(username: string, password: string) {
  const user = await prisma.user.findUnique({ where: { username } });
  if (!user) {
    throw new AppError("用户名或密码错误", 401);
  }

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    throw new AppError("用户名或密码错误", 401);
  }

  if (user.status === "disabled") {
    throw new AppError("账号已被禁用", 403);
  }

  const token = generateToken(user.userId, user.role);

  await prisma.auditLog.create({
    data: {
      operatorId: user.userId,
      action: "login",
      targetType: "user",
      targetId: user.userId,
      detail: { username: user.username },
    },
  });

  return { token, role: user.role, userId: user.userId };
}

export async function refreshToken(oldToken: string) {
  const { verifyToken } = await import("@/Lib/JwtHelper");
  const payload = verifyToken(oldToken);
  if (!payload) {
    throw new AppError("认证令牌无效或已过期", 401);
  }

  const user = await prisma.user.findUnique({
    where: { userId: payload.userId },
  });
  if (!user || user.status === "disabled") {
    throw new AppError("用户不存在或已被禁用", 401);
  }

  const token = generateToken(user.userId, user.role);
  return { token, role: user.role, userId: user.userId };
}