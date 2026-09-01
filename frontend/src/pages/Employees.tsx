import React, {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  createEmployee,
  deleteEmployee,
  getEmployees,
  updateEmployee,
} from "../api/employee.api";

import {
  getApiErrorMessage,
} from "../api/error";

import type {
  Employee,
  EmployeeCreate,
  EmployeeUpdate,
} from "../types/employee";

import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";


interface EmployeeForm {

  employee_code: string;

  full_name: string;

  email: string;

  department: string;

  user_id: string;
}


const emptyForm: EmployeeForm = {

  employee_code: "",

  full_name: "",

  email: "",

  department: "",

  user_id: "",
};


export default function Employees() {

  const navigate = useNavigate();

  const location = useLocation();


  /*
  |--------------------------------------------------------------------------
  | Employee state
  |--------------------------------------------------------------------------
  */

  const [
    employees,
    setEmployees,
  ] = useState<Employee[]>([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    loadError,
    setLoadError,
  ] = useState("");


  const [
    search,
    setSearch,
  ] = useState("");


  /*
  |--------------------------------------------------------------------------
  | Modal state
  |--------------------------------------------------------------------------
  */

  const [
    showModal,
    setShowModal,
  ] = useState(false);


  const [
    editingEmployee,
    setEditingEmployee,
  ] = useState<Employee | null>(null);


  const [
    form,
    setForm,
  ] = useState<EmployeeForm>(
    emptyForm
  );


  const [
    saving,
    setSaving,
  ] = useState(false);


  const [
    formError,
    setFormError,
  ] = useState("");


  /*
  |--------------------------------------------------------------------------
  | Delete state
  |--------------------------------------------------------------------------
  */

  const [
    deletingId,
    setDeletingId,
  ] = useState<number | null>(null);


  const [
    deleteError,
    setDeleteError,
  ] = useState("");


  /*
  |--------------------------------------------------------------------------
  | Current user
  |--------------------------------------------------------------------------
  */

  const user = useMemo(() => {

    try {

      return JSON.parse(
        localStorage.getItem("user") || "{}"
      );

    } catch {

      return {};

    }

  }, []);


  /*
  |--------------------------------------------------------------------------
  | Load employees
  |--------------------------------------------------------------------------
  */

  async function loadEmployees() {

    try {

      setLoading(true);

      setLoadError("");

      const data =
        await getEmployees();

      setEmployees(data);

    } catch (error) {

      console.error(
        "Failed to load employees:",
        error
      );

      setLoadError(
        getApiErrorMessage(error)
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadEmployees();

  }, []);


  /*
  |--------------------------------------------------------------------------
  | Search
  |--------------------------------------------------------------------------
  */

  const filteredEmployees =
    useMemo(() => {

      const keyword =
        search.trim().toLowerCase();

      if (!keyword) {
        return employees;
      }

      return employees.filter(
        (employee) => {

          return [

            employee.employee_code,

            employee.full_name,

            employee.email,

            employee.department || "",

            String(employee.user_id),

          ]
            .join(" ")
            .toLowerCase()
            .includes(keyword);
        }
      );

    }, [employees, search]);


  /*
  |--------------------------------------------------------------------------
  | Modal
  |--------------------------------------------------------------------------
  */

  function openCreateModal() {

    setEditingEmployee(null);

    setForm(emptyForm);

    setFormError("");

    setShowModal(true);
  }


  function openEditModal(
    employee: Employee
  ) {

    setEditingEmployee(employee);

    setForm({

      employee_code:
        employee.employee_code,

      full_name:
        employee.full_name,

      email:
        employee.email,

      department:
        employee.department || "",

      user_id:
        String(employee.user_id),

    });

    setFormError("");

    setShowModal(true);
  }


  function closeModal() {

    if (saving) {
      return;
    }

    setShowModal(false);

    setEditingEmployee(null);

    setForm(emptyForm);

    setFormError("");
  }


  function handleChange(
    field: keyof EmployeeForm,
    value: string
  ) {

    setForm((current) => ({

      ...current,

      [field]: value,

    }));

    setFormError("");
  }


  /*
  |--------------------------------------------------------------------------
  | Submit
  |--------------------------------------------------------------------------
  */

  async function handleSubmit(
    event: React.FormEvent
  ) {

    event.preventDefault();

    setFormError("");


    if (
      !form.employee_code.trim() ||
      !form.full_name.trim() ||
      !form.email.trim() ||
      !form.user_id.trim()
    ) {

      setFormError(
        "Please fill in all required fields."
      );

      return;
    }


    const userId =
      Number(form.user_id);


    if (
      !Number.isInteger(userId) ||
      userId <= 0
    ) {

      setFormError(
        "User ID must be a valid number."
      );

      return;
    }


    const data:
      EmployeeCreate | EmployeeUpdate = {

      employee_code:
        form.employee_code.trim(),

      full_name:
        form.full_name.trim(),

      email:
        form.email.trim(),

      department:
        form.department.trim()
          ? form.department.trim()
          : null,

      user_id:
        userId,
    };


    try {

      setSaving(true);

      setFormError("");


      if (editingEmployee) {

        const updated =
          await updateEmployee(
            editingEmployee.id,
            data
          );


        setEmployees(
          (current) =>
            current.map(
              (employee) =>
                employee.id ===
                editingEmployee.id
                  ? updated
                  : employee
            )
        );

      } else {

        const created =
          await createEmployee(
            data as EmployeeCreate
          );


        setEmployees(
          (current) => [
            ...current,
            created,
          ]
        );
      }


      closeModal();

    } catch (error) {

      console.error(
        "Failed to save employee:",
        error
      );

      setFormError(
        getApiErrorMessage(error)
      );

    } finally {

      setSaving(false);

    }
  }


  /*
  |--------------------------------------------------------------------------
  | Delete
  |--------------------------------------------------------------------------
  */

  async function handleDelete(
    employee: Employee
  ) {

    const confirmed =
      window.confirm(
        `Are you sure you want to delete ${employee.full_name}?`
      );


    if (!confirmed) {
      return;
    }


    try {

      setDeletingId(employee.id);

      setDeleteError("");


      await deleteEmployee(
        employee.id
      );


      setEmployees(
        (current) =>
          current.filter(
            (item) =>
              item.id !== employee.id
          )
      );

    } catch (error) {

      console.error(
        "Failed to delete employee:",
        error
      );

      setDeleteError(
        getApiErrorMessage(error)
      );

    } finally {

      setDeletingId(null);

    }
  }


  /*
  |--------------------------------------------------------------------------
  | Logout
  |--------------------------------------------------------------------------
  */

  function handleLogout() {

    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "user"
    );

    navigate(
      "/login",
      { replace: true }
    );
  }


  /*
  |--------------------------------------------------------------------------
  | Render
  |--------------------------------------------------------------------------
  */

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

          <Link
            to="/dashboard"
            className={
              `sidebar-link ${
                location.pathname ===
                "/dashboard"
                  ? "active"
                  : ""
              }`
            }
          >

            <span>▦</span>

            <span>
              Dashboard
            </span>

          </Link>


          <Link
            to="/employees"
            className={
              `sidebar-link ${
                location.pathname ===
                "/employees"
                  ? "active"
                  : ""
              }`
            }
          >

            <span>♙</span>

            <span>
              Employees
            </span>

          </Link>

        </nav>


        <div className="sidebar-bottom">

          <button
            className="sidebar-link"
            onClick={handleLogout}
            type="button"
          >

            <span>↪</span>

            <span>
              Logout
            </span>

          </button>


          <div className="sidebar-user">

            <div className="user-avatar">

              {
                user.username
                  ?.charAt(0)
                  ?.toUpperCase() || "U"
              }

            </div>


            <div>

              <div className="user-name">

                {
                  user.username ||
                  "User"
                }

              </div>

              <div className="user-role">

                {
                  user.role ||
                  "Employee"
                }

              </div>

            </div>

          </div>

        </div>

      </aside>


      {/* MAIN */}

      <main className="page-main">


        {/* HEADER */}

        <header className="page-header">

          <div className="page-title">

            <h1>
              Employees
            </h1>

            <p>
              Manage employee information
            </p>

          </div>


          <button
            className="primary-button"
            onClick={openCreateModal}
            type="button"
            disabled={loading}
          >
            + Add Employee
          </button>

        </header>


        {/* DELETE ERROR */}

        {deleteError && (

          <div className="error-alert">

            <span>⚠</span>

            <span>
              {deleteError}
            </span>

            <button
              type="button"
              onClick={() =>
                setDeleteError("")
              }
            >
              ×
            </button>

          </div>

        )}


        {/* EMPLOYEE CARD */}

        <section className="employee-card">


          {/* TOOLBAR */}

          <div className="employee-toolbar">

            <div className="search-wrapper">

              <span className="search-icon">
                🔍
              </span>

              <input
                className="search-input"
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                placeholder="Search by employee code, name, email or department..."
                disabled={loading}
              />

            </div>


            <div className="employee-count">

              {filteredEmployees.length}

              {" employee"}

              {
                filteredEmployees.length !==
                1
                  ? "s"
                  : ""
              }

            </div>

          </div>


          {/* CONTENT */}

          {loading ? (

            <Loading
              message="Loading employees..."
            />

          ) : loadError ? (

            <ErrorMessage
              message={loadError}
              onRetry={loadEmployees}
            />

          ) : filteredEmployees.length === 0 ? (

            <div className="empty-state">

              <div className="empty-icon">
                👥
              </div>

              <div>

                {
                  search
                    ? "No employees found."
                    : "No employees yet."
                }

              </div>

              {!search && (

                <button
                  type="button"
                  className="primary-button"
                  onClick={
                    openCreateModal
                  }
                >
                  + Add Employee
                </button>

              )}

            </div>

          ) : (

            <div className="employee-table-wrapper">

              <table className="employee-table">

                <thead>

                  <tr>

                    <th>
                      EMPLOYEE
                    </th>

                    <th>
                      NAME
                    </th>

                    <th>
                      EMAIL
                    </th>

                    <th>
                      DEPARTMENT
                    </th>

                    <th>
                      USER ID
                    </th>

                    <th>
                      ACTIONS
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {filteredEmployees.map(
                    (employee) => (

                      <tr
                        key={
                          employee.id
                        }
                      >

                        <td>

                          <span className="employee-code">

                            {
                              employee.employee_code
                            }

                          </span>

                        </td>


                        <td>

                          <div className="employee-info">

                            <div className="employee-avatar">

                              {
                                getInitials(
                                  employee.full_name
                                )
                              }

                            </div>

                            <div className="employee-name">

                              {
                                employee.full_name
                              }

                            </div>

                          </div>

                        </td>


                        <td>

                          <span className="employee-email">

                            {
                              employee.email
                            }

                          </span>

                        </td>


                        <td>

                          {
                            employee.department ? (

                              <span className="department-badge">

                                {
                                  employee.department
                                }

                              </span>

                            ) : (

                              <span>
                                —
                              </span>

                            )
                          }

                        </td>


                        <td>

                          <span className="user-id">

                            #
                            {
                              employee.user_id
                            }

                          </span>

                        </td>


                        <td>

                          <div className="action-buttons">

                            <button
                              className="action-button"
                              title="Edit employee"
                              type="button"
                              onClick={() =>
                                openEditModal(
                                  employee
                                )
                              }
                              disabled={
                                deletingId !==
                                null
                              }
                            >
                              ✎
                            </button>


                            <button
                              className="action-button delete"
                              title="Delete employee"
                              type="button"
                              onClick={() =>
                                handleDelete(
                                  employee
                                )
                              }
                              disabled={
                                deletingId ===
                                employee.id
                              }
                            >

                              {
                                deletingId ===
                                employee.id
                                  ? "..."
                                  : "🗑"
                              }

                            </button>

                          </div>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>

      </main>


      {/* MODAL */}

      {showModal && (

        <div
          className="modal-overlay"
          onMouseDown={(event) => {

            if (
              event.target ===
              event.currentTarget
            ) {

              closeModal();

            }

          }}
        >

          <div className="modal">


            {/* MODAL HEADER */}

            <div className="modal-header">

              <h2>

                {
                  editingEmployee
                    ? "Edit Employee"
                    : "Add Employee"
                }

              </h2>


              <button
                className="modal-close"
                type="button"
                onClick={closeModal}
                disabled={saving}
              >
                ×
              </button>

            </div>


            <form
              onSubmit={handleSubmit}
            >

              <div className="modal-body">


                {/* FORM ERROR */}

                {formError && (

                  <div className="error-alert">

                    <span>
                      ⚠
                    </span>

                    <span>
                      {formError}
                    </span>

                  </div>

                )}


                {/* EMPLOYEE CODE */}

                <div className="modal-form-group">

                  <label className="modal-form-label">

                    Employee Code

                    <span className="required">
                      *
                    </span>

                  </label>


                  <input
                    className="modal-input"
                    value={
                      form.employee_code
                    }
                    onChange={(event) =>
                      handleChange(
                        "employee_code",
                        event.target.value
                      )
                    }
                    placeholder="EMP001"
                    required
                    disabled={saving}
                  />

                </div>


                {/* FULL NAME */}

                <div className="modal-form-group">

                  <label className="modal-form-label">

                    Full Name

                    <span className="required">
                      *
                    </span>

                  </label>


                  <input
                    className="modal-input"
                    value={
                      form.full_name
                    }
                    onChange={(event) =>
                      handleChange(
                        "full_name",
                        event.target.value
                      )
                    }
                    placeholder="Nguyen Van A"
                    required
                    disabled={saving}
                  />

                </div>


                {/* EMAIL */}

                <div className="modal-form-group">

                  <label className="modal-form-label">

                    Email

                    <span className="required">
                      *
                    </span>

                  </label>


                  <input
                    className="modal-input"
                    type="email"
                    value={
                      form.email
                    }
                    onChange={(event) =>
                      handleChange(
                        "email",
                        event.target.value
                      )
                    }
                    placeholder="employee@gmail.com"
                    required
                    disabled={saving}
                  />

                </div>


                {/* DEPARTMENT */}

                <div className="modal-form-group">

                  <label className="modal-form-label">

                    Department

                  </label>


                  <input
                    className="modal-input"
                    value={
                      form.department
                    }
                    onChange={(event) =>
                      handleChange(
                        "department",
                        event.target.value
                      )
                    }
                    placeholder="IT"
                    disabled={saving}
                  />

                </div>


                {/* USER ID */}

                <div className="modal-form-group">

                  <label className="modal-form-label">

                    User ID

                    <span className="required">
                      *
                    </span>

                  </label>


                  <input
                    className="modal-input"
                    type="number"
                    min="1"
                    value={
                      form.user_id
                    }
                    onChange={(event) =>
                      handleChange(
                        "user_id",
                        event.target.value
                      )
                    }
                    placeholder="2"
                    required
                    disabled={saving}
                  />

                </div>

              </div>


              {/* FOOTER */}

              <div className="modal-footer">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >

                  {
                    saving
                      ? "Saving..."
                      : editingEmployee
                        ? "Save Changes"
                        : "Create Employee"
                  }

                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  );
}


/*
|--------------------------------------------------------------------------
| Helpers
|--------------------------------------------------------------------------
*/

function getInitials(
  name: string
) {

  return name
    .trim()
    .split(/\s+/)
    .map(
      (part) => part[0]
    )
    .join("")
    .slice(-2)
    .toUpperCase();
}