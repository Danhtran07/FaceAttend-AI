import { useEffect, useState, type FormEvent } from "react";
import { Clock3, MoonStar, Plus, ShieldCheck } from "lucide-react";

import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { getApiErrorMessage } from "../api/error";
import { createShift, getShifts, type ShiftCreate } from "../api/schedule.api";
import type { Shift } from "../types/schedule";

function formatTime(value: string) {
  return value.slice(0, 5);
}

export default function Shifts() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [form, setForm] = useState<ShiftCreate>({
    name: "",
    code: "",
    description: null,
    start_time: "08:00:00",
    end_time: "17:00:00",
    break_start_time: null,
    break_end_time: null,
    late_tolerance_minutes: 15,
    early_checkin_minutes: 30,
    is_overnight: false,
    is_active: true,
  });

  async function loadShifts() {
    try {
      setLoading(true);
      setError("");
      setShifts(await getShifts());
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to load shifts."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadShifts(); }, []);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError("");
    try {
      setSaving(true);
      const created = await createShift(form);
      setShifts((current) => [...current, created]);
      setFormOpen(false);
      setForm((current) => ({ ...current, name: "", code: "", description: null }));
    } catch (err) {
      setFormError(getApiErrorMessage(err, "Unable to create shift."));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState message="Loading shifts..." />;
  if (error) return <ErrorState message={error} onRetry={() => void loadShifts()} />;

  const activeCount = shifts.filter((shift) => shift.is_active).length;
  const overnightCount = shifts.filter((shift) => shift.is_overnight).length;

  return (
    <section className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">Work configuration</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Shifts</h1>
          <p className="mt-1 text-sm text-slate-500">Define the time windows and grace periods used by attendance policy.</p>
        </div>
        <div className="flex items-center gap-3"><div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm font-semibold text-blue-700">{activeCount} active shift{activeCount === 1 ? "" : "s"}</div><button type="button" onClick={() => { setFormError(""); setFormOpen(true); }} className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-bold text-white hover:bg-slate-700"><Plus size={17} />Create shift</button></div>
      </header>

      {formOpen && <form onSubmit={handleCreate} className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-2 lg:grid-cols-4">
        <input required placeholder="Shift name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <input required placeholder="Code" value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <label className="text-sm text-slate-600">Start<input required type="time" value={form.start_time.slice(0, 5)} onChange={(event) => setForm({ ...form, start_time: `${event.target.value}:00` })} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
        <label className="text-sm text-slate-600">End<input required type="time" value={form.end_time.slice(0, 5)} onChange={(event) => setForm({ ...form, end_time: `${event.target.value}:00` })} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2" /></label>
        <div className="flex gap-3 sm:col-span-2 lg:col-span-4"><button disabled={saving} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">{saving ? "Saving..." : "Save shift"}</button><button type="button" onClick={() => setFormOpen(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-bold text-slate-700">Cancel</button>{formError && <p className="self-center text-sm text-rose-600">{formError}</p>}</div>
      </form>}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><Clock3 className="text-blue-600" size={20} /><p className="mt-4 text-2xl font-bold text-slate-900">{shifts.length}</p><p className="text-sm text-slate-500">Configured shifts</p></div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><ShieldCheck className="text-emerald-600" size={20} /><p className="mt-4 text-2xl font-bold text-slate-900">{activeCount}</p><p className="text-sm text-slate-500">Available for assignment</p></div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><MoonStar className="text-violet-600" size={20} /><p className="mt-4 text-2xl font-bold text-slate-900">{overnightCount}</p><p className="text-sm text-slate-500">Overnight shifts</p></div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-4"><h2 className="font-bold text-slate-900">Shift library</h2><p className="mt-1 text-sm text-slate-500">Policy values are captured in attendance records when employees check in.</p></div>
        {shifts.length === 0 ? <div className="px-5 py-16 text-center text-sm text-slate-500">No shifts have been configured yet.</div> : <div className="divide-y divide-slate-100">{shifts.map((shift) => <article key={shift.id} className="flex flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between"><div className="flex items-start gap-4"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Clock3 size={20} /></div><div><div className="flex flex-wrap items-center gap-2"><h3 className="font-bold text-slate-900">{shift.name}</h3><span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-slate-500">{shift.code}</span>{!shift.is_active && <span className="rounded-md bg-rose-50 px-2 py-1 text-[10px] font-bold uppercase text-rose-600">Inactive</span>}</div><p className="mt-1 text-sm text-slate-500">{formatTime(shift.start_time)} - {formatTime(shift.end_time)}{shift.is_overnight ? " · overnight" : ""}</p></div></div><div className="grid grid-cols-2 gap-3 text-sm md:min-w-[260px]"><div className="rounded-lg bg-slate-50 px-3 py-2"><p className="text-xs text-slate-400">Late tolerance</p><p className="mt-1 font-bold text-slate-800">{shift.late_tolerance_minutes} min</p></div><div className="rounded-lg bg-slate-50 px-3 py-2"><p className="text-xs text-slate-400">Early check-in</p><p className="mt-1 font-bold text-slate-800">{shift.early_checkin_minutes} min</p></div></div></article>)}</div>}
      </div>
    </section>
  );
}