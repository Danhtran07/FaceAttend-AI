import apiClient from "./client";
import type {
  Attendance,
  AttendanceCalendarResponse,
  AttendanceCreate,
  AttendanceUpdate,
} from "../types/attendance";

export async function getAttendanceCalendar(
  year: number,
  month: number,
  employeeId?: number
): Promise<AttendanceCalendarResponse> {
  const response = await apiClient.get<AttendanceCalendarResponse>(
    "/api/attendance/calendar",
    {
      params: {
        year,
        month,
        ...(employeeId ? { employee_id: employeeId } : {}),
      },
    }
  );

  return response.data;
}

export async function getAttendances(): Promise<Attendance[]> {
  const response = await apiClient.get<Attendance[]>(
    "/api/attendance"
  );

  return response.data;
}

export async function getAttendance(
  id: number
): Promise<Attendance> {
  const response = await apiClient.get<Attendance>(
    `/api/attendance/${id}`
  );

  return response.data;
}

export async function createAttendance(
  data: AttendanceCreate
): Promise<Attendance> {
  const response = await apiClient.post<Attendance>(
    "/api/attendance",
    data
  );

  return response.data;
}

export async function updateAttendance(
  id: number,
  data: AttendanceUpdate
): Promise<Attendance> {
  const response = await apiClient.put<Attendance>(
    `/api/attendance/${id}`,
    data
  );

  return response.data;
}

export async function deleteAttendance(
  id: number
): Promise<void> {
  await apiClient.delete(`/api/attendance/${id}`);
}