import apiClient from "./client";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginUser {
  id: number;
  username: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: LoginUser;
}

export async function login(
  data: LoginRequest
): Promise<LoginResponse> {
  const response =
    await apiClient.post<LoginResponse>(
      "/api/auth/login",
      data
    );

  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/api/auth/logout");
}