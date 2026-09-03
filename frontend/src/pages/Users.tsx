import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  createUser,
  deleteUser,
  getUsers,
  updateUser,
} from "../api/user.api";

import type {
  UserCreate,
  UserResponse,
  UserRole,
  UserUpdate,
} from "../types/user";

import { getApiErrorMessage } from "../api/error";

interface UserForm {
  username: string;
  password: string;
  role: UserRole;
}

const initialForm: UserForm = {
  username: "",
  password: "",
  role: "EMPLOYEE",
};

export default function Users() {
  const [users, setUsers] =
    useState<UserResponse[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [modalOpen, setModalOpen] =
    useState(false);

  const [editingUser, setEditingUser] =
    useState<UserResponse | null>(null);

  const [form, setForm] =
    useState<UserForm>(initialForm);

  const [saving, setSaving] =
    useState(false);

  const [deletingId, setDeletingId] =
    useState<number | null>(null);

  const [formError, setFormError] =
    useState("");

  async function loadUsers() {
    try {
      setLoading(true);
      setError("");

      const data = await getUsers();

      setUsers(data);
    } catch (err) {
      setError(
        getApiErrorMessage(
          err,
          "Unable to load users."
        )
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  function openCreateModal() {
    setEditingUser(null);
    setForm(initialForm);
    setFormError("");
    setModalOpen(true);
  }

  function openEditModal(
    user: UserResponse
  ) {
    setEditingUser(user);

    setForm({
      username: user.username,
      password: "",
      role: user.role,
    });

    setFormError("");
    setModalOpen(true);
  }

  function closeModal() {
    if (saving) return;

    setModalOpen(false);
    setEditingUser(null);
    setForm(initialForm);
    setFormError("");
  }

  function updateForm(
    field: keyof UserForm,
    value: string
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setFormError("");

    if (!form.username.trim()) {
      setFormError(
        "Username is required."
      );
      return;
    }

    if (
      !editingUser &&
      !form.password.trim()
    ) {
      setFormError(
        "Password is required."
      );
      return;
    }

    try {
      setSaving(true);

      if (editingUser) {
        const data: UserUpdate = {
          username:
            form.username.trim(),
          role: form.role,
        };

        if (form.password.trim()) {
          data.password =
            form.password;
        }

        const updated =
          await updateUser(
            editingUser.id,
            data
          );

        setUsers((current) =>
          current.map((item) =>
            item.id === updated.id
              ? updated
              : item
          )
        );
      } else {
        const data: UserCreate = {
          username:
            form.username.trim(),
          password:
            form.password,
          role: form.role,
        };

        const created =
          await createUser(data);

        setUsers((current) => [
          ...current,
          created,
        ]);
      }

      closeModal();
    } catch (err) {
      setFormError(
        getApiErrorMessage(
          err,
          "Unable to save user."
        )
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(
    user: UserResponse
  ) {
    const confirmed =
      window.confirm(
        `Delete user "${user.username}"?`
      );

    if (!confirmed) return;

    try {
      setDeletingId(user.id);

      await deleteUser(user.id);

      setUsers((current) =>
        current.filter(
          (item) =>
            item.id !== user.id
        )
      );
    } catch (err) {
      setError(
        getApiErrorMessage(
          err,
          "Unable to delete user."
        )
      );
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            User Management
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Manage system accounts and
            access roles.
          </p>
        </div>

        <button
          type="button"
          onClick={openCreateModal}
          className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
        >
          + Add User
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 sm:flex-row sm:items-center sm:justify-between">
          <span>{error}</span>

          <button
            type="button"
            onClick={loadUsers}
            className="font-semibold underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex min-h-[300px] items-center justify-center">
            <div className="flex items-center gap-3 text-sm text-slate-500">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />
              Loading users...
            </div>
          </div>
        ) : users.length === 0 ? (
          <div className="flex min-h-[300px] flex-col items-center justify-center px-6 text-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-2xl">
              👤
            </div>

            <h2 className="font-semibold text-slate-800">
              No users found
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Create the first user account.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                    ID
                  </th>

                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                    Username
                  </th>

                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                    Role
                  </th>

                  <th className="px-6 py-4 text-right text-xs font-bold uppercase tracking-wider text-slate-500">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="transition hover:bg-slate-50"
                  >
                    <td className="px-6 py-4 text-sm text-slate-500">
                      #{user.id}
                    </td>

                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-800">
                        {user.username}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${
                          user.role ===
                          "ADMIN"
                            ? "bg-purple-100 text-purple-700"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {user.role}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            openEditModal(
                              user
                            )
                          }
                          className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600"
                        >
                          Edit
                        </button>

                        <button
                          type="button"
                          disabled={
                            deletingId ===
                            user.id
                          }
                          onClick={() =>
                            handleDelete(
                              user
                            )
                          }
                          className="rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {deletingId ===
                          user.id
                            ? "Deleting..."
                            : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl">
            <div className="border-b border-slate-100 px-6 py-5">
              <h2 className="text-lg font-bold text-slate-900">
                {editingUser
                  ? "Edit User"
                  : "Add User"}
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {editingUser
                  ? "Update account information."
                  : "Create a new system account."}
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="space-y-5 p-6"
            >
              {formError && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {formError}
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Username
                </label>

                <input
                  value={form.username}
                  onChange={(event) =>
                    updateForm(
                      "username",
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                  placeholder="Enter username"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Password
                </label>

                <input
                  type="password"
                  value={form.password}
                  onChange={(event) =>
                    updateForm(
                      "password",
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                  placeholder={
                    editingUser
                      ? "Leave blank to keep current password"
                      : "Enter password"
                  }
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-700">
                  Role
                </label>

                <select
                  value={form.role}
                  onChange={(event) =>
                    updateForm(
                      "role",
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-50"
                >
                  <option value="EMPLOYEE">
                    EMPLOYEE
                  </option>

                  <option value="ADMIN">
                    ADMIN
                  </option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  disabled={saving}
                  className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {saving
                    ? "Saving..."
                    : editingUser
                    ? "Save Changes"
                    : "Create User"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}