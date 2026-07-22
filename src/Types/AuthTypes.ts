export interface RegisterRequest {
  username: string;
  password: string;
  role: "patient";
  realName: string;
  phone: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  role: "patient" | "doctor" | "follower" | "admin";
  userId: string;
}

export interface RegisterResponse {
  userId: string;
  token: string;
  role: string;
}

export interface RefreshResponse {
  token: string;
  role: string;
  userId: string;
}