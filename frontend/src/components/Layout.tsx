import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();

  const user = JSON.parse(
    localStorage.getItem("user") || "{}"
  );

  const username = user.username || "User";
  const role = user.role || "EMPLOYEE";

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    navigate("/login", { replace: true });
  }

  return (
    <div className="app-layout">

      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">

        {/* Logo */}

        <div className="sidebar-brand">

          <div className="brand-icon">
            F
          </div>

          <div>
            <div className="brand-name">
              FaceAttend
            </div>

            <div className="brand-subtitle">
              Attendance System
            </div>
          </div>

        </div>

        {/* Navigation */}

        <nav className="sidebar-nav">

          <div className="nav-section-title">
            MAIN MENU
          </div>

          <Link
            to="/dashboard"
            className={`nav-item ${
              location.pathname === "/dashboard"
                ? "active"
                : ""
            }`}
          >
            <span className="nav-icon">
              ▦
            </span>

            <span>
              Dashboard
            </span>
          </Link>

          <Link
            to="/employees"
            className={`nav-item ${
              location.pathname.startsWith("/employees")
                ? "active"
                : ""
            }`}
          >
            <span className="nav-icon">
              ♙
            </span>

            <span>
              Employees
            </span>
          </Link>

        </nav>

        {/* Bottom */}

        <div className="sidebar-bottom">

          <div className="sidebar-user">

            <div className="sidebar-avatar">
              {username
                .charAt(0)
                .toUpperCase()}
            </div>

            <div className="sidebar-user-info">

              <div className="sidebar-username">
                {username}
              </div>

              <div className="sidebar-role">
                {role}
              </div>

            </div>

          </div>

          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
          >
            <span>↪</span>
            Logout
          </button>

        </div>

      </aside>

      {/* ================= MAIN ================= */}

      <div className="app-content">

        {/* Topbar */}

        <header className="topbar">

          <div>
            <span className="topbar-title">
              FaceAttend
            </span>
          </div>

          <div className="topbar-right">

            <div className="topbar-status">
              <span className="status-dot" />
              System Online
            </div>

            <div className="topbar-user">
              {username}
            </div>

          </div>

        </header>

        {/* Page */}

        <main className="page-content">
          <Outlet />
        </main>

      </div>

    </div>
  );
}