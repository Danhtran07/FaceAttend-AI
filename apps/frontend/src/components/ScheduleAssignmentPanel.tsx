import { useEffect, useState, type FormEvent } from "react";
import { UserRoundPlus } from "lucide-react";

import { getApiErrorMessage } from "../api/error";
import { getEmployees } from "../api/employee.api";
import {
  createScheduleAssignment,
  getSchedules,
} from "../api/schedule.api";
import type { Employee } from "../types/employee";
import type { WorkSchedule } from "../types/schedule";

export default function ScheduleAssignmentPanel() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [schedules, setSchedules] = useState<WorkSchedule[]>([]);
  const [employeeId, setEmployeeId] = useState("");
  const [scheduleId, setScheduleId] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState(new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getEmployees(), getSchedules()])
      .then(([employeeData, scheduleData]) => {
        setEmployees(employeeData);
        setSchedules(scheduleData);
        if (employeeData[0]) setEmployeeId(String(employeeData[0].id));
        if (scheduleData[0]) setScheduleId(String(scheduleData[0].id));
      })
      .catch((err) => setError(getApiErrorMessage(err, "Unable to load assignment options.")));
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      setSaving(true);
      const assignment = await createScheduleAssignment({
        employee_id: Number(employeeId),
        schedule_id: Number(scheduleId),
        effective_from: effectiveFrom,
        is_active: true,
      });
      setMessage(`${assignment.employee_name} is assigned to ${assignment.schedule_name}.`);
    } catch (err) {
      setError(getApiErrorMessage(err, "Unable to assign schedule."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
      <div className="flex items-center gap-3">
        <UserRoundPlus className="text-blue-600" size={20} />
        <div>
          <h2 className="font-bold text-slate-900">Assign schedule to employee</h2>
          <p className="mt-1 text-sm text-slate-500">The schedule determines the employee's shift for each weekday.</p>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <select required value={employeeId} onChange={(event) => setEmployeeId(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
          {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.employee_code} - {employee.full_name}</option>)}
        </select>
        <select required value={scheduleId} onChange={(event) => setScheduleId(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
          {schedules.map((schedule) => <option key={schedule.id} value={schedule.id}>{schedule.name} ({schedule.code})</option>)}
        </select>
        <input required type="date" value={effectiveFrom} onChange={(event) => setEffectiveFrom(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <button disabled={saving || !employeeId || !scheduleId} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-50">{saving ? "Assigning..." : "Assign schedule"}</button>
        {message && <span className="text-sm font-semibold text-emerald-700">{message}</span>}
        {error && <span className="text-sm font-semibold text-rose-600">{error}</span>}
      </div>
    </form>
  );
}
