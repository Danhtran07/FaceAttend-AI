export interface Employee {

  id: number;

  employee_code: string;

  full_name: string;

  email: string;

  department: string | null;

  user_id: number;

  created_at?: string;

  updated_at?: string;
}


export interface EmployeeCreate {

  employee_code: string;

  full_name: string;

  email: string;

  department: string | null;

  user_id: number;
}


export interface EmployeeUpdate {

  employee_code?: string;

  full_name?: string;

  email?: string;

  department?: string | null;

  user_id?: number;
}