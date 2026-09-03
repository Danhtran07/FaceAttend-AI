export type AttendanceStatus =
  | "PRESENT"
  | "LATE"
  | "ABSENT";

export interface Attendance {
  id: number;
  employee_id: number;
  date: string;
  check_in: string | null;
  check_out: string | null;
  status: AttendanceStatus;
  created_at: string;
  updated_at: string;
}

export interface AttendanceCreate {
  employee_id: number;
  date: string;
  check_in?: string | null;
  check_out?: string | null;
  status: AttendanceStatus;
}

export interface AttendanceUpdate {
  check_in?: string | null;
  check_out?: string | null;
  status?: AttendanceStatus;
}