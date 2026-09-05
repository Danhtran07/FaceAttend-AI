import apiClient from "./client";
import type {
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
} from "../types/employee";

export async function enrollEmployeeFace(
  id: number,
  image: File
): Promise<void> {
  const formData = new FormData();
  formData.append("image", image);
  await apiClient.post(`/api/employees/${id}/face`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
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