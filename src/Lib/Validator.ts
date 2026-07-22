const USERNAME_REGEX = /^[a-zA-Z0-9_]{3,50}$/;
const PHONE_REGEX = /^1[3-9]\d{9}$/;

export function validateUsername(username: string): boolean {
  return USERNAME_REGEX.test(username);
}

export function validatePhone(phone: string): boolean {
  return PHONE_REGEX.test(phone);
}

export function validatePassword(password: string): boolean {
  return password.length >= 8 && password.length <= 64;
}

export function validatePagination(
  page?: number,
  pageSize?: number
): { page: number; pageSize: number } {
  return {
    page: Math.max(1, page ?? 1),
    pageSize: Math.min(100, Math.max(1, pageSize ?? 20)),
  };
}