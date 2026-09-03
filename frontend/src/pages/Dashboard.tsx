import { useMemo } from "react";

interface StoredUser {
  username?: string;
  role?: string;
}

const statistics = [
  {
    label: "Total Employees",
    value: "128",
    description: "+8.2% this month",
    icon: "👥",
    iconClass: "bg-blue-50 text-blue-600",
  },
  {
    label: "Present Today",
    value: "112",
    description: "87.5% attendance rate",
    icon: "✓",
    iconClass: "bg-emerald-50 text-emerald-600",
  },
  {
    label: "Late Today",
    value: "9",
    description: "-3 from yesterday",
    icon: "◷",
    iconClass: "bg-amber-50 text-amber-600",
  },
  {
    label: "Absent Today",
    value: "7",
    description: "5.5% of employees",
    icon: "!",
    iconClass: "bg-red-50 text-red-600",
  },
];

const weeklyAttendance = [
  {
    day: "Monday",
    percent: 92,
  },
  {
    day: "Tuesday",
    percent: 88,
  },
  {
    day: "Wednesday",
    percent: 95,
  },
  {
    day: "Thursday",
    percent: 91,
  },
  {
    day: "Friday",
    percent: 87,
  },
];

const recentAttendance = [
  {
    name: "Nguyen Van A",
    time: "08:01 AM",
  },
  {
    name: "Tran Thi B",
    time: "08:04 AM",
  },
  {
    name: "Le Van C",
    time: "08:07 AM",
  },
  {
    name: "Pham Thi D",
    time: "08:12 AM",
  },
  {
    name: "Hoang Van E",
    time: "08:15 AM",
  },
];

export default function Dashboard() {
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

  const today =
    new Date().toLocaleDateString(
      "en-US",
      {
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
      }
    );

  return (
    <div className="mx-auto w-full max-w-[1600px]">

      {/* =====================================================
          PAGE HEADER
      ===================================================== */}

      <header
        className="
          mb-7
          flex flex-col
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


        <div
          className="
            inline-flex
            w-fit
            items-center
            rounded-xl
            border border-slate-200
            bg-white
            px-4 py-2.5
            text-sm font-medium
            text-slate-500
            shadow-sm
          "
        >
          {today}
        </div>

      </header>


      {/* =====================================================
          STATISTICS
      ===================================================== */}

      <section
        className="
          grid
          grid-cols-1
          gap-5
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >

        {statistics.map((stat) => (
          <div
            key={stat.label}
            className="
              rounded-2xl
              border border-slate-200
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
                  flex h-11 w-11
                  items-center justify-center
                  rounded-xl
                  text-lg font-bold
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
                text-emerald-600
              "
            >
              {stat.description}
            </div>

          </div>
        ))}

      </section>


      {/* =====================================================
          MAIN DASHBOARD
      ===================================================== */}

      <section
        className="
          mt-6
          grid
          grid-cols-1
          gap-6
          xl:grid-cols-[1.3fr_1fr]
        "
      >

        {/* ===================================================
            ATTENDANCE OVERVIEW
        =================================================== */}

        <div
          className="
            rounded-2xl
            border border-slate-200
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
                px-3 py-1.5
                text-xs font-semibold
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
                  key={item.day}
                  day={item.day}
                  percent={item.percent}
                />
              )
            )}

          </div>

        </div>


        {/* ===================================================
            RECENT ATTENDANCE
        =================================================== */}

        <div
          className="
            rounded-2xl
            border border-slate-200
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
                px-3 py-1.5
                text-xs font-semibold
                text-slate-500
              "
            >
              Today
            </span>

          </div>


          <div className="mt-5 divide-y divide-slate-100">

            {recentAttendance.map(
              (item) => (
                <Activity
                  key={`${item.name}-${item.time}`}
                  name={item.name}
                  time={item.time}
                />
              )
            )}

          </div>

        </div>

      </section>


      {/* =====================================================
          DEMO DATA NOTICE
      ===================================================== */}

      <div
        className="
          mt-6
          flex
          items-start
          gap-3
          rounded-2xl
          border border-blue-100
          bg-blue-50/60
          p-4
        "
      >

        <div
          className="
            flex h-8 w-8
            shrink-0
            items-center justify-center
            rounded-full
            bg-blue-100
            text-xs font-bold
            text-blue-600
          "
        >
          i
        </div>

        <div>

          <div
            className="
              text-xs
              font-bold
              text-blue-900
            "
          >
            Demo data
          </div>

          <p
            className="
              mt-1
              text-xs
              leading-5
              text-blue-700
            "
          >
            Dashboard statistics and attendance
            activity are currently sample data.
            They will be connected to the
            Attendance API in the next development phase.
          </p>

        </div>

      </div>

    </div>
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
}: {
  name: string;
  time: string;
}) {
  const initials = name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(-2)
    .toUpperCase();

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
          flex h-10 w-10
          shrink-0
          items-center justify-center
          rounded-full
          bg-blue-50
          text-xs font-bold
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
        className="
          shrink-0
          rounded-lg
          bg-emerald-50
          px-2.5 py-1.5
          text-[11px]
          font-bold
          text-emerald-600
        "
      >
        Present
      </span>

    </div>
  );
}