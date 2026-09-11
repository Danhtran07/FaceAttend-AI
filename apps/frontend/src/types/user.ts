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

export interface Profile {
  id: number;
  user_id: number;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  avatar_url: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
}

export type ProfileUpdate = Pick<Profile, "full_name" | "email" | "phone" | "avatar_url" | "bio">;