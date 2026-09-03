export type UserRole =
  | "ADMIN"
  | "EMPLOYEE";

export interface UserResponse {
  id: number;
  username: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  username: string;
  password: string;
  role: UserRole;
}

export interface UserUpdate {
  username?: string;
  password?: string;
  role?: UserRole;
}