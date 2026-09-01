import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "./Login";
import Dashboard from "./Dashboard";
import Employees from "./Employees";

import ProtectedRoute from "../components/ProtectedRoute";
import Layout from "../components/Layout";

export default function App() {
  return (
    <BrowserRouter>

      <Routes>

        {/* ================= PUBLIC ================= */}

        <Route
          path="/login"
          element={<Login />}
        />

        {/* ================= PROTECTED ================= */}

        <Route element={<ProtectedRoute />}>

          <Route element={<Layout />}>

            <Route
              path="/dashboard"
              element={<Dashboard />}
            />

            <Route
              path="/employees"
              element={<Employees />}
            />

          </Route>

        </Route>

        {/* ================= DEFAULT ================= */}

        <Route
          path="/"
          element={
            <Navigate
              to="/dashboard"
              replace
            />
          }
        />

        {/* ================= NOT FOUND ================= */}

        <Route
          path="*"
          element={
            <Navigate
              to="/dashboard"
              replace
            />
          }
        />

      </Routes>

    </BrowserRouter>
  );
}