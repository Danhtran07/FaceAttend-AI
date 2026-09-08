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

export type ShiftCreate = Omit<Shift, "id">;

export async function createShift(data: ShiftCreate): Promise<Shift> {
  const response = await apiClient.post<Shift>("/api/shifts", data);
  return response.data;
}

export interface ScheduleAssignmentCreate {
  employee_id: number;
  schedule_id: number;
  effective_from: string;
  effective_to?: string | null;
  is_active: boolean;
}

export interface ScheduleAssignment {
  id: number;
  employee_id: number;
  employee_code: string;
  employee_name: string;
  schedule_id: number;
  schedule_name: string;
  effective_from: string;
  effective_to: string | null;
  is_active: boolean;
}

export async function createScheduleAssignment(
  data: ScheduleAssignmentCreate,
): Promise<ScheduleAssignment> {
  const response = await apiClient.post<ScheduleAssignment>(
    "/api/schedule-assignments",
    data,
  );
  return response.data;
}