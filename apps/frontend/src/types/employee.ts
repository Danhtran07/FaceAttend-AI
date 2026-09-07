export interface Employee {

  id: number;

  employee_code: string;

  full_name: string;

  email: string;

  department: string | null;

  user_id: number;
  face_enrolled: boolean;

  created_at?: string;

  updated_at?: string;
}


export interface EmployeeCreate {
  full_name: string;

  email: string;

  department: string | null;
}


export interface EmployeeUpdate {

  employee_code?: string;

  full_name?: string;

  email?: string;

  department?: string | null;

  user_id?: number;
}