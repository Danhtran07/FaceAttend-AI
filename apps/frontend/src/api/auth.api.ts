import apiClient from "./client";
import type { Profile, ProfileUpdate } from "../types/user";

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

export async function getProfile(): Promise<Profile> {
  const response = await apiClient.get<Profile>("/api/profile");
  return response.data;
}

export async function updateProfile(data: ProfileUpdate): Promise<Profile> {
  const response = await apiClient.put<Profile>("/api/profile", data);
  return response.data;
}

export async function uploadProfileAvatar(file: File): Promise<Profile> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post<Profile>("/api/profile/avatar", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}