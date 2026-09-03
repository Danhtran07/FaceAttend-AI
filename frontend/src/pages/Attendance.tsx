import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import { useEffect, useMemo, useState } from "react";
import {
  createAttendance,
  deleteAttendance,
  getAttendances,
  updateAttendance,
} from "../api/attendance.api";
import { getEmployees } from "../api/employee.api";
import { getApiErrorMessage } from "../api/error";

import type {
  Attendance,
  AttendanceCreate,
  AttendanceStatus,
  AttendanceUpdate,
} from "../types/attendance";

import type { Employee } from "../types/employee";

const EMPTY_FORM: AttendanceCreate = {
  employee_id: 0,
  date: "",
  check_in: "",
  check_out: "",
  status: "PRESENT",
};

function statusClass(status: AttendanceStatus) {
  switch (status) {
    case "PRESENT":
      return "bg-green-100 text-green-700";

    case "LATE":
      return "bg-yellow-100 text-yellow-700";

    case "ABSENT":
      return "bg-red-100 text-red-700";

    default:
      return "bg-gray-100 text-gray-700";
  }
}

function formatDateTime(value: string | null) {
  if (!value) return "-";

  return new Date(value).toLocaleString("vi-VN");
}

export default function Attendance() {
  const [attendances, setAttendances] = useState<Attendance[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [dateFilter, setDateFilter] = useState("");
  const [employeeFilter, setEmployeeFilter] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] =
    useState<AttendanceCreate>(EMPTY_FORM);

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [attendanceData, employeeData] =
        await Promise.all([
          getAttendances(),
          getEmployees(),
        ]);

      setAttendances(attendanceData);
      setEmployees(employeeData);
    } catch (err) {
      setError(
        getApiErrorMessage(
          err,
          "Unable to load attendance data."
        )
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const employeeMap = useMemo(() => {
    const map = new Map<number, Employee>();

    employees.forEach((employee) => {
      map.set(employee.id, employee);
    });

    return map;
  }, [employees]);

  const filteredAttendances = useMemo(() => {
    return attendances.filter((item) => {
      const matchDate =
        !dateFilter ||
        item.date.startsWith(dateFilter);

      const matchEmployee =
        !employeeFilter ||
        String(item.employee_id) === employeeFilter;

      return matchDate && matchEmployee;
    });
  }, [
    attendances,
    dateFilter,
    employeeFilter,
  ]);

  function openCreate() {
    setEditingId(null);

    setForm({
      ...EMPTY_FORM,
      employee_id:
        employees.length > 0
          ? employees[0].id
          : 0,
    });

    setError("");
    setSuccess("");
    setShowModal(true);
  }

  function openEdit(item: Attendance) {
    setEditingId(item.id);

    setForm({
      employee_id: item.employee_id,
      date: item.date,
      check_in: item.check_in
        ? item.check_in.slice(0, 16)
        : "",
      check_out: item.check_out
        ? item.check_out.slice(0, 16)
        : "",
      status: item.status,
    });

    setError("");
    setSuccess("");
    setShowModal(true);
  }

  function closeModal() {
    if (saving) return;

    setShowModal(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!form.employee_id) {
      setError("Please select an employee.");
      return;
    }

    if (!form.date) {
      setError("Please select attendance date.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      if (editingId === null) {
        await createAttendance({
          ...form,
          check_in: form.check_in || null,
          check_out: form.check_out || null,
        });

        setSuccess(
          "Attendance created successfully."
        );
      } else {
        const updateData: AttendanceUpdate = {
  check_in: form.check_in || null,
  check_out: form.check_out || null,
  status: form.status,
};

        await updateAttendance(
          editingId,
          updateData
        );

        setSuccess(
          "Attendance updated successfully."
        );
      }

      setShowModal(false);
      await loadData();
    } catch (err) {
      setError(
        getApiErrorMessage(
          err,
          "Failed to save attendance."
        )
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this attendance record?"
    );

    if (!confirmed) return;

    try {
      setError("");
      setSuccess("");

      await deleteAttendance(id);

      setSuccess(
        "Attendance deleted successfully."
      );

      await loadData();
    } catch (err) {
      setError(
        getApiErrorMessage(
          err,
          "Failed to delete attendance."
        )
      );
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Attendance
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Manage employee attendance records.
          </p>
        </div>

        <button
          type="button"
          onClick={openCreate}
          disabled={employees.length === 0}
          className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          + Add Attendance
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </div>
      )}

      {/* Filters */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Date
            </label>

            <input
              type="date"
              value={dateFilter}
              onChange={(e) =>
                setDateFilter(e.target.value)
              }
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Employee
            </label>

            <select
              value={employeeFilter}
              onChange={(e) =>
                setEmployeeFilter(e.target.value)
              }
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            >
              <option value="">
                All employees
              </option>

              {employees.map((employee) => (
                <option
                  key={employee.id}
                  value={employee.id}
                >
                  {employee.full_name} (
                  {employee.employee_code})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="button"
              onClick={() => {
                setDateFilter("");
                setEmployeeFilter("");
              }}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Clear filters
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
  <LoadingState message="Loading attendance..." />
) : error ? (
  <ErrorState
    message={error}
    onRetry={loadData}
  />
) : filteredAttendances.length === 0 ? (
  <EmptyState
    title="No attendance records"
    message="No attendance records match your filters."
  />
) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Employee
                  </th>

                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Date
                  </th>

                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Check-in
                  </th>

                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Check-out
                  </th>

                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Status
                  </th>

                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-gray-100">
                {filteredAttendances.map((item) => {
                  const employee =
                    employeeMap.get(
                      item.employee_id
                    );

                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-6 py-4">
                        <div className="font-medium text-gray-900">
                          {employee?.full_name ??
                            `Employee #${item.employee_id}`}
                        </div>

                        {employee && (
                          <div className="text-xs text-gray-500">
                            {employee.employee_code}
                          </div>
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-700">
                        {item.date}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-700">
                        {formatDateTime(
                          item.check_in
                        )}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-700">
                        {formatDateTime(
                          item.check_out
                        )}
                      </td>

                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${statusClass(
                            item.status
                          )}`}
                        >
                          {item.status}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() =>
                              openEdit(item)
                            }
                            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(item.id)
                            }
                            className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  {editingId === null
                    ? "Add Attendance"
                    : "Edit Attendance"}
                </h2>

                <p className="text-sm text-gray-500">
                  Enter attendance information.
                </p>
              </div>

              <button
                type="button"
                onClick={closeModal}
                className="text-xl text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <form
              onSubmit={handleSubmit}
              className="space-y-4"
            >
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Employee
                </label>

                <select
                  value={form.employee_id}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      employee_id: Number(
                        e.target.value
                      ),
                    })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  required
                >
                  <option value={0}>
                    Select employee
                  </option>

                  {employees.map((employee) => (
                    <option
                      key={employee.id}
                      value={employee.id}
                    >
                      {employee.full_name} (
                      {employee.employee_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Date
                </label>

                <input
                  type="date"
                  value={form.date}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      date: e.target.value,
                    })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  required
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Check-in
                  </label>

                  <input
                    type="datetime-local"
                    value={form.check_in ?? ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        check_in:
                          e.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Check-out
                  </label>

                  <input
                    type="datetime-local"
                    value={form.check_out ?? ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        check_out:
                          e.target.value,
                      })
                    }
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Status
                </label>

                <select
                  value={form.status}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      status:
                        e.target
                          .value as AttendanceStatus,
                    })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  <option value="PRESENT">
                    PRESENT
                  </option>
                  <option value="LATE">
                    LATE
                  </option>
                  <option value="ABSENT">
                    ABSENT
                  </option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving
                    ? "Saving..."
                    : editingId === null
                    ? "Create"
                    : "Update"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}