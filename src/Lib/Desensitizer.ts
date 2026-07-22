export function desensitizeRealName(name: string): string {
  if (name.length <= 1) return "*";
  return name[0] + "*".repeat(name.length - 1);
}

export function desensitizePhone(phone: string): string {
  if (phone.length < 7) return phone;
  return phone.slice(0, 3) + "****" + phone.slice(-4);
}