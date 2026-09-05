import apiClient from "./client";
import type { RecognitionAttendanceResponse } from "../types/recognition";

export async function recognizeAttendance(
  image: Blob,
  livenessSessionId?: string
): Promise<RecognitionAttendanceResponse> {
  const formData = new FormData();
  formData.append("image", image, "face-capture.jpg");

  if (livenessSessionId) {
    formData.append("liveness_session_id", livenessSessionId);
  }

  const response = await apiClient.post<RecognitionAttendanceResponse>(
    "/api/attendance/recognize",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  return response.data;
}