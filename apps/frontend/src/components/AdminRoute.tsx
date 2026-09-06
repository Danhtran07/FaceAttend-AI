import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

interface AdminRouteProps {
  children: ReactNode;
}

interface StoredUser {
  role?: string;
}

export default function AdminRoute({
  children,
}: AdminRouteProps) {
  const token =
    localStorage.getItem("access_token");

  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  let user: StoredUser = {};

  try {
    const storedUser =
      localStorage.getItem("user");

    user = storedUser
      ? JSON.parse(storedUser)
      : {};
  } catch {
    user = {};
  }

  if (user.role !== "ADMIN") {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  return <>{children}</>;
}