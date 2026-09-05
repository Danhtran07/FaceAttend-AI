import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { getEmployees } from "../api/employee.api";
import { getAttendances } from "../api/attendance.api";
import { getApiErrorMessage } from "../api/error";

import type { Employee } from "../types/employee";
import type { Attendance } from "../types/attendance";

import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";


/* ============================================================
   TYPES
============================================================ */

interface StoredUser {
  username?: string;
  role?: string;
}

interface Statistic {
  label: string;
  value: number;
  description: string;
  icon: string;
  iconClass: string;
}


/* ============================================================
   DASHBOARD
============================================================ */

export default function Dashboard() {

  /* ==========================================================
     USER
  ========================================================== */

  const user = useMemo<StoredUser>(() => {
    const storedUser =
      localStorage.getItem("user");

    if (!storedUser) {
      return {};
    }

    try {
      return JSON.parse(storedUser);
    } catch {
      return {};
    }
  }, []);

  const username =
    user.username || "User";


  /* ==========================================================
     STATE
  ========================================================== */

  const [employees, setEmployees] =
    useState<Employee[]>([]);

  const [attendances, setAttendances] =
    useState<Attendance[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  /* ==========================================================
     LOAD DASHBOARD DATA
  ========================================================== */

  async function loadDashboard() {

    try {

      setLoading(true);
      setError("");

      const [
        employeeData,
        attendanceData,
      ] = await Promise.all([
        getEmployees(),
        getAttendances(),
      ]);

      setEmployees(employeeData);
      setAttendances(attendanceData);

    } catch (err) {

      setError(
        getApiErrorMessage(
          err,
          "Unable to load dashboard data."
        )
      );

    } finally {

      setLoading(false);

    }
  }


  /* ==========================================================
     INITIAL LOAD
  ========================================================== */

  useEffect(() => {
    loadDashboard();
  }, []);


  /* ==========================================================
     DATE
  ========================================================== */

  const today =
    new Date()
      .toISOString()
      .split("T")[0];


  const displayDate =
    new Date().toLocaleDateString(
      "en-US",
      {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
      }
    );


  /* ==========================================================
     TODAY ATTENDANCE
  ========================================================== */

  const todayAttendances =
    useMemo(() => {

      return attendances.filter(
        (item) =>
          item.date === today
      );

    }, [attendances, today]);


  /* ==========================================================
     STATISTICS
  ========================================================== */

  const totalEmployees =
    employees.length;


  const presentCount =
    todayAttendances.filter(
      (item) =>
        item.status === "PRESENT"
    ).length;


  const lateCount =
    todayAttendances.filter(
      (item) =>
        item.status === "LATE"
    ).length;


  const absentCount =
    todayAttendances.filter(
      (item) =>
        item.status === "ABSENT"
    ).length;


  /* ==========================================================
     ATTENDANCE RATE
  ========================================================== */

  const attendanceRate =
    totalEmployees > 0
      ? Math.round(
          ((presentCount + lateCount) /
            totalEmployees) *
            100
        )
      : 0;


  /* ==========================================================
     EMPLOYEE MAP
  ========================================================== */

  const employeeMap =
    useMemo(() => {

      const map =
        new Map<number, Employee>();

      employees.forEach(
        (employee) => {
          map.set(
            employee.id,
            employee
          );
        }
      );

      return map;

    }, [employees]);


  /* ==========================================================
     STATISTIC CARDS
  ========================================================== */

  const statistics: Statistic[] = [
    {
      label: "Total Employees",
      value: totalEmployees,
      description:
        "Registered employees",
      icon: "👥",
      iconClass:
        "bg-blue-50 text-blue-600",
    },

    {
      label: "Present Today",
      value: presentCount,
      description:
        `${attendanceRate}% attendance rate`,
      icon: "✓",
      iconClass:
        "bg-emerald-50 text-emerald-600",
    },

    {
      label: "Late Today",
      value: lateCount,
      description:
        "Today's late employees",
      icon: "◷",
      iconClass:
        "bg-amber-50 text-amber-600",
    },

    {
      label: "Absent Today",
      value: absentCount,
      description:
        "Recorded absences",
      icon: "!",
      iconClass:
        "bg-red-50 text-red-600",
    },
  ];


  /* ==========================================================
     RECENT ATTENDANCE
  ========================================================== */

  const recentAttendance =
    useMemo(() => {

      return [...todayAttendances]
        .sort((a, b) => {

          const timeA =
            a.check_in
              ? new Date(
                  a.check_in
                ).getTime()
              : Number.MAX_SAFE_INTEGER;

          const timeB =
            b.check_in
              ? new Date(
                  b.check_in
                ).getTime()
              : Number.MAX_SAFE_INTEGER;

          return timeA - timeB;

        })
        .slice(0, 5);

    }, [todayAttendances]);


  /* ==========================================================
     WEEKLY ATTENDANCE
  ========================================================== */

  const weeklyAttendance =
    useMemo(() => {

      const result: {
        day: string;
        date: string;
        percent: number;
      }[] = [];

      const now = new Date();

      const dayOfWeek =
        now.getDay();

      const mondayOffset =
        dayOfWeek === 0
          ? -6
          : 1 - dayOfWeek;

      const monday =
        new Date(now);

      monday.setDate(
        now.getDate() +
          mondayOffset
      );

      for (let i = 0; i < 5; i++) {

        const date =
          new Date(monday);

        date.setDate(
          monday.getDate() + i
        );

        const dateString =
          date
            .toISOString()
            .split("T")[0];

        const dayAttendances =
          attendances.filter(
            (item) =>
              item.date === dateString
          );

        const validCount =
          dayAttendances.filter(
            (item) =>
              item.status ===
                "PRESENT" ||
              item.status ===
                "LATE"
          ).length;

        const percent =
          totalEmployees > 0
            ? Math.round(
                (validCount /
                  totalEmployees) *
                  100
              )
            : 0;

        result.push({
          day:
            date.toLocaleDateString(
              "en-US",
              {
                weekday: "long",
              }
            ),

          date: dateString,

          percent,
        });
      }

      return result;

    }, [
      attendances,
      totalEmployees,
    ]);


  /* ==========================================================
     LOADING
  ========================================================== */

  if (loading) {

    return (
      <LoadingState
        message="Loading dashboard..."
      />
    );

  }


  /* ==========================================================
     ERROR
  ========================================================== */

  if (error) {

    return (
      <ErrorState
        message={error}
        onRetry={loadDashboard}
      />
    );

  }


  /* ==========================================================
     EMPTY
  ========================================================== */

  if (
    employees.length === 0 &&
    attendances.length === 0
  ) {

    return (
      <div className="mx-auto w-full max-w-[1600px]">

        <header className="mb-7">

          <div
            className="
              mb-1
              text-[11px]
              font-bold
              uppercase
              tracking-[0.12em]
              text-blue-600
            "
          >
            Overview
          </div>

          <h1
            className="
              text-2xl
              font-extrabold
              tracking-tight
              text-slate-900
              sm:text-3xl
            "
          >
            Dashboard
          </h1>

          <p className="mt-1.5 text-sm text-slate-500">
            Welcome back,{" "}
            <span className="font-semibold text-slate-700">
              {username}
            </span>
          </p>

        </header>

        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">

          <EmptyState
            title="No dashboard data"
            message="There is no employee or attendance data available."
          />

        </div>

      </div>
    );

  }


  /* ==========================================================
     MAIN UI
  ========================================================== */

  return (

    <div className="mx-auto w-full max-w-[1600px]">


      {/* ======================================================
          PAGE HEADER
      ====================================================== */}

      <header
        className="
          mb-7
          flex
          flex-col
          gap-4
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >

        <div>

          <div
            className="
              mb-1
              text-[11px]
              font-bold
              uppercase
              tracking-[0.12em]
              text-blue-600
            "
          >
            Overview
          </div>

          <h1
            className="
              text-2xl
              font-extrabold
              tracking-tight
              text-slate-900
              sm:text-3xl
            "
          >
            Dashboard
          </h1>

          <p
            className="
              mt-1.5
              text-sm
              text-slate-500
            "
          >
            Welcome back,{" "}

            <span className="font-semibold text-slate-700">
              {username}
            </span>
          </p>

        </div>


        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/recognition"
            className="
              inline-flex
              items-center
              gap-2
              rounded-xl
              bg-blue-600
              px-4
              py-2.5
              text-sm
              font-bold
              text-white
              no-underline
              shadow-sm
              transition
              hover:bg-blue-700
              hover:shadow-md
            "
          >
            <span aria-hidden="true">◉</span>
            Face Attendance
          </Link>

          <div
            className="
              inline-flex
              w-fit
              items-center
              rounded-xl
              border
              border-slate-200
              bg-white
              px-4
              py-2.5
              text-sm
              font-medium
              text-slate-500
              shadow-sm
            "
          >
            {displayDate}
          </div>
        </div>

      </header>


      {/* ======================================================
          STATISTICS
      ====================================================== */}

      <section
        className="
          grid
          grid-cols-1
          gap-5
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >

        {statistics.map(
          (stat) => (

            <div
              key={stat.label}
              className="
                rounded-2xl
                border
                border-slate-200
                bg-white
                p-5
                shadow-sm
                transition
                hover:-translate-y-0.5
                hover:shadow-md
              "
            >

              <div
                className="
                  flex
                  items-start
                  justify-between
                "
              >

                <div
                  className="
                    text-xs
                    font-semibold
                    text-slate-500
                  "
                >
                  {stat.label}
                </div>

                <div
                  className={`
                    flex
                    h-11
                    w-11
                    items-center
                    justify-center
                    rounded-xl
                    text-lg
                    font-bold
                    ${stat.iconClass}
                  `}
                >
                  {stat.icon}
                </div>

              </div>


              <div
                className="
                  mt-5
                  text-3xl
                  font-extrabold
                  tracking-tight
                  text-slate-900
                "
              >
                {stat.value}
              </div>


              <div
                className="
                  mt-2
                  text-xs
                  font-semibold
                  text-slate-500
                "
              >
                {stat.description}
              </div>

            </div>

          )
        )}

      </section>


      {/* ======================================================
          MAIN DASHBOARD
      ====================================================== */}

      <section
        className="
          mt-6
          grid
          grid-cols-1
          gap-6
          xl:grid-cols-[1.3fr_1fr]
        "
      >


        {/* ====================================================
            ATTENDANCE OVERVIEW
        ==================================================== */}

        <div
          className="
            rounded-2xl
            border
            border-slate-200
            bg-white
            p-5
            shadow-sm
            sm:p-6
          "
        >

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <h2
                className="
                  text-base
                  font-bold
                  text-slate-900
                "
              >
                Attendance Overview
              </h2>

              <p
                className="
                  mt-1
                  text-xs
                  text-slate-400
                "
              >
                Employee attendance rate during this week
              </p>

            </div>


            <span
              className="
                shrink-0
                rounded-lg
                bg-slate-50
                px-3
                py-1.5
                text-xs
                font-semibold
                text-slate-500
              "
            >
              This week
            </span>

          </div>


          <div className="mt-8 space-y-5">

            {weeklyAttendance.map(
              (item) => (

                <AttendanceRow
                  key={item.date}
                  day={item.day}
                  percent={item.percent}
                />

              )
            )}

          </div>

        </div>


        {/* ====================================================
            RECENT ATTENDANCE
        ==================================================== */}

        <div
          className="
            rounded-2xl
            border
            border-slate-200
            bg-white
            p-5
            shadow-sm
            sm:p-6
          "
        >

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <h2
                className="
                  text-base
                  font-bold
                  text-slate-900
                "
              >
                Recent Attendance
              </h2>

              <p
                className="
                  mt-1
                  text-xs
                  text-slate-400
                "
              >
                Latest employee check-ins
              </p>

            </div>


            <span
              className="
                shrink-0
                rounded-lg
                bg-slate-50
                px-3
                py-1.5
                text-xs
                font-semibold
                text-slate-500
              "
            >
              Today
            </span>

          </div>


          <div className="mt-5 divide-y divide-slate-100">

            {recentAttendance.length === 0 ? (

              <div className="py-8">

                <EmptyState
                  title="No attendance today"
                  message="No employee check-ins have been recorded today."
                />

              </div>

            ) : (

              recentAttendance.map(
                (item) => {

                  const employee =
                    employeeMap.get(
                      item.employee_id
                    );

                  return (
                    <Activity
                      key={item.id}
                      name={
                        employee?.full_name ??
                        `Employee #${item.employee_id}`
                      }
                      time={
                        item.check_in
                          ? formatTime(
                              item.check_in
                            )
                          : "-"
                      }
                      status={
                        item.status
                      }
                    />
                  );

                }
              )

            )}

          </div>

        </div>

      </section>


      {/* ======================================================
          REFRESH
      ====================================================== */}

      <div
        className="
          mt-6
          flex
          items-center
          justify-between
          rounded-2xl
          border
          border-slate-200
          bg-white
          p-4
          shadow-sm
        "
      >

        <div>

          <div
            className="
              text-xs
              font-bold
              text-slate-700
            "
          >
            Dashboard data
          </div>

          <p
            className="
              mt-1
              text-xs
              text-slate-400
            "
          >
            Data is loaded from Employees and Attendance APIs.
          </p>

        </div>


        <button
          type="button"
          onClick={loadDashboard}
          className="
            rounded-lg
            border
            border-slate-200
            bg-white
            px-4
            py-2
            text-xs
            font-semibold
            text-slate-600
            transition
            hover:bg-slate-50
            hover:text-blue-600
          "
        >
          Refresh
        </button>

      </div>

    </div>
  );
}


/* ============================================================
   FORMAT TIME
============================================================ */

function formatTime(
  value: string
) {

  return new Date(
    value
  ).toLocaleTimeString(
    "vi-VN",
    {
      hour: "2-digit",
      minute: "2-digit",
    }
  );

}


/* ============================================================
   ATTENDANCE ROW
============================================================ */

function AttendanceRow({
  day,
  percent,
}: {
  day: string;
  percent: number;
}) {

  return (

    <div
      className="
        grid
        grid-cols-[80px_1fr_48px]
        items-center
        gap-3
      "
    >

      <span
        className="
          text-xs
          font-semibold
          text-slate-500
        "
      >
        {day}
      </span>


      <div
        className="
          h-2
          overflow-hidden
          rounded-full
          bg-slate-100
        "
      >

        <div
          className="
            h-full
            rounded-full
            bg-blue-600
            transition-all
            duration-500
          "
          style={{
            width: `${percent}%`,
          }}
        />

      </div>


      <span
        className="
          text-right
          text-xs
          font-bold
          text-slate-500
        "
      >
        {percent}%
      </span>

    </div>

  );
}


/* ============================================================
   ACTIVITY
============================================================ */

function Activity({
  name,
  time,
  status,
}: {
  name: string;
  time: string;
  status: string;
}) {

  const initials =
    name
      .trim()
      .split(/\s+/)
      .map(
        (part) => part[0]
      )
      .join("")
      .slice(-2)
      .toUpperCase();


  const statusClass =
    status === "PRESENT"
      ? "bg-emerald-50 text-emerald-600"
      : status === "LATE"
      ? "bg-amber-50 text-amber-600"
      : "bg-red-50 text-red-600";


  return (

    <div
      className="
        flex
        items-center
        gap-3
        py-4
      "
    >

      <div
        className="
          flex
          h-10
          w-10
          shrink-0
          items-center
          justify-center
          rounded-full
          bg-blue-50
          text-xs
          font-bold
          text-blue-600
        "
      >
        {initials}
      </div>


      <div className="min-w-0 flex-1">

        <div
          className="
            truncate
            text-sm
            font-bold
            text-slate-800
          "
        >
          {name}
        </div>


        <div
          className="
            mt-1
            text-xs
            text-slate-400
          "
        >
          Checked in at {time}
        </div>

      </div>


      <span
        className={`
          shrink-0
          rounded-lg
          px-2.5
          py-1.5
          text-[11px]
          font-bold
          ${statusClass}
        `}
      >
        {status}
      </span>

    </div>

  );
}