import apiClient from "./client";
import type { EmployeeSchedule, Shift, WorkSchedule } from "../types/schedule";

export async function getShifts(): Promise<Shift[]> {
  const response = await apiClient.get<Shift[]>("/api/shifts");
  return response.data;
}

export async function getSchedules(): Promise<WorkSchedule[]> {
  const response = await apiClient.get<WorkSchedule[]>("/api/schedules");
  return response.data;
}

export async function getEmployeeSchedule(
  employeeId: number,
  targetDate: string,
): Promise<EmployeeSchedule> {
  const response = await apiClient.get<EmployeeSchedule>(
    `/api/employees/${employeeId}/schedule`,
    { params: { target_date: targetDate } },
  );
  return response.data;
}

export async function getMySchedule(targetDate: string): Promise<EmployeeSchedule> {
  const response = await apiClient.get<EmployeeSchedule>(
    "/api/schedules/me",
    { params: { target_date: targetDate } },
  );
  return response.data;
}