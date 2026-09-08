import { useEffect, useState } from "react";
import { CalendarDays, Clock3 } from "lucide-react";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import ScheduleAssignmentPanel from "../components/ScheduleAssignmentPanel";
import { getApiErrorMessage } from "../api/error";
import { getSchedules } from "../api/schedule.api";
import type { WorkSchedule } from "../types/schedule";

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function formatTime(value: string) {
  return value.slice(0, 5);
}

export default function SchedulesAdmin() {
  const [schedules, setSchedules] = useState<WorkSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadSchedules() {
    try {
      setLoading(true);
      setError("");
      setSchedules(await getSchedules());
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to load schedules."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadSchedules(); }, []);
  if (loading) return <LoadingState message="Loading schedules..." />;
  if (error) return <ErrorState message={error} onRetry={() => void loadSchedules()} />;

  return (
    <section className="space-y-6">
      <header>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">Work configuration</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Schedules</h1>
        <p className="mt-1 text-sm text-slate-500">Create weekly patterns, then assign them to employees.</p>
      </header>
      <ScheduleAssignmentPanel />
      <div className="grid gap-5 xl:grid-cols-2">
        {schedules.map((schedule) => {
          const rules = new Map(schedule.rules.map((rule) => [rule.day_of_week, rule]));
          return <article key={schedule.id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-start justify-between border-b border-slate-100 px-5 py-5">
              <div className="flex gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 text-violet-600"><CalendarDays size={20} /></div><div><h2 className="font-bold text-slate-900">{schedule.name}</h2><p className="mt-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{schedule.code}</p></div></div>
              <span className={`rounded-md px-2 py-1 text-[10px] font-bold uppercase ${schedule.is_active ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-500"}`}>{schedule.is_active ? "Active" : "Inactive"}</span>
            </div>
            <div className="grid grid-cols-1 divide-y divide-slate-100 px-5 py-2 sm:grid-cols-2 sm:divide-y-0 sm:gap-x-6">
              {days.map((day, index) => { const shift = rules.get(index + 1)?.shift; return <div key={day} className="flex items-center justify-between py-3"><span className="text-sm font-semibold text-slate-600">{day}</span>{shift ? <span className="flex items-center gap-1.5 text-xs font-bold text-slate-800"><Clock3 size={14} className="text-blue-500" />{shift.name} · {formatTime(shift.start_time)}</span> : <span className="text-xs font-medium text-slate-400">Day off</span>}</div>; })}
            </div>
          </article>;
        })}
      </div>
      {schedules.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center text-sm text-slate-500">No schedules have been configured yet.</div>}
    </section>
  );
}
