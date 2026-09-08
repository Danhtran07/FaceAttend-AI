export type NotificationSeverity = "INFO" | "WARNING" | "URGENT" | "SUCCESS";

export type NotificationType =
  | "CHECK_IN_REMINDER"
  | "CHECK_IN_MISSING"
  | "LATE_CHECK_IN"
  | "CHECK_IN_SUCCESS"
  | "CHECK_OUT_REMINDER"
  | "CHECK_OUT_MISSING"
  | "CHECK_OUT_SUCCESS"
  | "LEAVE_APPROVED"
  | "LEAVE_REJECTED"
  | "OT_PENDING"
  | "OT_APPROVED"
  | "OT_REJECTED"
  | "ATTENDANCE_ANOMALY";

export interface Notification {
  id: number;
  notification_type: NotificationType;
  severity: NotificationSeverity;
  attendance_date: string;
  title: string;
  message: string;
  action_label: string | null;
  action_path: string | null;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}
