import { Link, useLocation, useNavigate } from "react-router-dom";
import { logout } from "../api/auth.api";

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();

  const user = JSON.parse(
    localStorage.getItem("user") || "{}"
  );

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Backend logout may fail if token has expired.
    }

    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    navigate("/login");
  }

  const menu = [
    {
      path: "/dashboard",
      icon: "▦",
      label: "Dashboard",
    },
    {
      path: "/employees",
      icon: "♙",
      label: "Employees",
    },
  ];

  return (
    <div className="dashboard-layout">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            F
          </div>

          <div className="sidebar-logo-text">
            FaceAttend
          </div>
        </div>

        <nav className="sidebar-menu">
          {menu.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-link ${
                location.pathname === item.path
                  ? "active"
                  : ""
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <button
            className="sidebar-link"
            onClick={handleLogout}
          >
            <span>↪</span>
            <span>Logout</span>
          </button>

          <div className="sidebar-user">
            <div className="user-avatar">
              {user.username
                ?.charAt(0)
                ?.toUpperCase() || "U"}
            </div>

            <div>
              <div className="user-name">
                {user.username || "User"}
              </div>

              <div className="user-role">
                {user.role || "Employee"}
              </div>
            </div>
          </div>

        </div>
      </aside>

      {/* MAIN */}
      <main className="dashboard-main">

        <header className="dashboard-header">
          <div className="dashboard-title">
            <h1>Dashboard</h1>

            <p>
              Welcome back,{" "}
              <strong>
                {user.username || "User"}
              </strong>
            </p>
          </div>

          <div className="header-date">
            {new Date().toLocaleDateString(
              "en-US",
              {
                weekday: "short",
                year: "numeric",
                month: "short",
                day: "numeric",
              }
            )}
          </div>
        </header>

        {/* STATISTICS */}
        <section className="stats-grid">

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">
                Total Employees
              </span>

              <div className="stat-icon">
                👥
              </div>
            </div>

            <div className="stat-value">
              128
            </div>

            <div className="stat-change">
              +8.2% this month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">
                Present Today
              </span>

              <div className="stat-icon">
                ✓
              </div>
            </div>

            <div className="stat-value">
              112
            </div>

            <div className="stat-change">
              87.5% attendance rate
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">
                Late Today
              </span>

              <div className="stat-icon">
                ◷
              </div>
            </div>

            <div className="stat-value">
              9
            </div>

            <div className="stat-change">
              -3 from yesterday
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-top">
              <span className="stat-label">
                Absent Today
              </span>

              <div className="stat-icon">
                !
              </div>
            </div>

            <div className="stat-value">
              7
            </div>

            <div className="stat-change">
              5.5% of employees
            </div>
          </div>

        </section>

        {/* CONTENT */}
        <section className="dashboard-grid">

          {/* ATTENDANCE */}
          <div className="dashboard-card">

            <div className="card-header">
              <h2>Attendance Overview</h2>
              <span>This week</span>
            </div>

            <div className="attendance-bars">

              <AttendanceRow
                day="Monday"
                percent={92}
              />

              <AttendanceRow
                day="Tuesday"
                percent={88}
              />

              <AttendanceRow
                day="Wednesday"
                percent={95}
              />

              <AttendanceRow
                day="Thursday"
                percent={91}
              />

              <AttendanceRow
                day="Friday"
                percent={87}
              />

            </div>
          </div>

          {/* RECENT ACTIVITY */}
          <div className="dashboard-card">

            <div className="card-header">
              <h2>Recent Attendance</h2>
              <span>Today</span>
            </div>

            <div className="activity-list">

              <Activity
                name="Nguyen Van A"
                time="08:01 AM"
              />

              <Activity
                name="Tran Thi B"
                time="08:04 AM"
              />

              <Activity
                name="Le Van C"
                time="08:07 AM"
              />

              <Activity
                name="Pham Thi D"
                time="08:12 AM"
              />

              <Activity
                name="Hoang Van E"
                time="08:15 AM"
              />

            </div>

          </div>

        </section>

      </main>
    </div>
  );
}

function AttendanceRow({
  day,
  percent,
}: {
  day: string;
  percent: number;
}) {
  return (
    <div className="attendance-row">

      <span>{day}</span>

      <div className="attendance-bar">
        <div
          className="attendance-fill"
          style={{ width: `${percent}%` }}
        />
      </div>

      <span className="attendance-percent">
        {percent}%
      </span>

    </div>
  );
}

function Activity({
  name,
  time,
}: {
  name: string;
  time: string;
}) {
  const initials = name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(-2);

  return (
    <div className="activity-item">

      <div className="activity-avatar">
        {initials}
      </div>

      <div className="activity-info">
        <div className="activity-name">
          {name}
        </div>

        <div className="activity-time">
          Checked in at {time}
        </div>
      </div>

      <div className="activity-status">
        Present
      </div>

    </div>
  );
}