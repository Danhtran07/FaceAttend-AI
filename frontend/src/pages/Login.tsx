import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth.api";
import { getApiErrorMessage } from "../api/error";

export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("12345678");
  const [loading, setLoading] =
  useState(false);

const [error, setError] =
  useState("");

  async function handleSubmit(
  event: React.FormEvent
) {

  event.preventDefault();

  setError("");

  setLoading(true);

  try {

    const response =
      await login({
        username,
        password,
      });


    localStorage.setItem(
      "access_token",
      response.access_token
    );


    localStorage.setItem(
      "user",
      JSON.stringify(
        response.user
      )
    );


    navigate(
      "/dashboard",
      { replace: true }
    );

  } catch (error) {

    console.error(
      "Login failed:",
      error
    );

    setError(
      getApiErrorMessage(error)
    );

  } finally {

    setLoading(false);

  }
}

  return (
    <div className="login-page">
      <div className="login-container">

        <div className="login-brand">
          <div className="brand-logo">F</div>

          <h1>FaceAttend</h1>

          <p>
            Smart attendance management system
            powered by facial recognition technology.
          </p>

          <div className="brand-features">
            <div className="brand-feature">
              <span className="feature-icon">✓</span>
              <span>Fast and accurate attendance</span>
            </div>

            <div className="brand-feature">
              <span className="feature-icon">✓</span>
              <span>Real-time employee management</span>
            </div>

            <div className="brand-feature">
              <span className="feature-icon">✓</span>
              <span>Secure authentication</span>
            </div>
          </div>
        </div>

        <div className="login-form-wrapper">
          <form
            className="login-form"
            onSubmit={handleSubmit}
          >
            <h2>Welcome back</h2>

            <p className="login-subtitle">
              Sign in to your FaceAttend account
            </p>

            <div className="form-group">
              <label className="form-label">
                Username
              </label>

              <input
                className="form-input"
                type="text"
                value={username}
                onChange={(e) =>
                  setUsername(e.target.value)
                }
                placeholder="Enter your username"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                Password
              </label>

              <input
                className="form-input"
                type="password"
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            <button
              className="login-button"
              type="submit"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>

            <div className="login-footer">
              FaceAttend AI · Attendance Management
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}