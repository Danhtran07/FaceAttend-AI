import apiClient from "./client";
import type { Notification } from "../types/notification";

export async function getNotifications(): Promise<Notification[]> {
  const response = await apiClient.get<Notification[]>("/api/notifications");
  return response.data;
}

export async function getUnreadNotificationCount(): Promise<number> {
  const response = await apiClient.get<{ unread_count: number }>(
    "/api/notifications/unread-count",
  );
  return response.data.unread_count;
}

export async function markNotificationRead(id: number): Promise<Notification> {
  const response = await apiClient.patch<Notification>(
    `/api/notifications/${id}/read`,
  );
  return response.data;
}
