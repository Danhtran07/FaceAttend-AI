import apiClient from "./client";
import type {
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
} from "../types/employee";

export async function enrollEmployeeFace(
  id: number,
  images: File[]
): Promise<{ embeddings_saved: number }> {
  const formData = new FormData();
  images.forEach((image) => formData.append("images", image));
  const response = await apiClient.post<{ embeddings_saved: number }>(
    `/api/employees/${id}/face`,
    formData,
    {
    headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}

export async function getEmployees(): Promise<Employee[]> {

  const response =
    await apiClient.get<Employee[]>(
      "/api/employees"
    );

  return response.data;
}

export async function createEmployee(
  data: EmployeeCreate
): Promise<Employee> {

  const response =
    await apiClient.post<Employee>(
      "/api/employees",
      data
    );

  return response.data;
}

export async function updateEmployee(
  id: number,
  data: EmployeeUpdate
): Promise<Employee> {

  const response =
    await apiClient.put<Employee>(
      `/api/employees/${id}`,
      data
    );

  return response.data;
}

export async function deleteEmployee(
  id: number
): Promise<void> {

  await apiClient.delete(
    `/api/employees/${id}`
  );
}