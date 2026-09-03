import apiClient from "./client";

import type {
  UserResponse,
  UserCreate,
  UserUpdate,
} from "../types/user";

export async function getUsers(): Promise<UserResponse[]> {
  const response = await apiClient.get<UserResponse[]>(
    "/api/users"
  );

  return response.data;
}

export async function getUser(
  id: number
): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>(
    `/api/users/${id}`
  );

  return response.data;
}

export async function createUser(
  data: UserCreate
): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>(
    "/api/users",
    data
  );

  return response.data;
}

export async function updateUser(
  id: number,
  data: UserUpdate
): Promise<UserResponse> {
  const response = await apiClient.put<UserResponse>(
    `/api/users/${id}`,
    data
  );

  return response.data;
}

export async function deleteUser(
  id: number
): Promise<void> {
  await apiClient.delete(`/api/users/${id}`);
}