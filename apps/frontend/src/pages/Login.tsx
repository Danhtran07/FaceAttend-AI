import {
  FormEvent,
  useState,
} from "react";
import { Check, LockKeyhole, CircleAlert } from "lucide-react";

import {
  useNavigate,
} from "react-router-dom";

import {
  login,
} from "../api/auth.api";

import {
  getApiErrorMessage,
} from "../api/error";


export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  /* ==========================================================
     LOGIN
  ========================================================== */

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");

    /* Prevent duplicate requests */

    if (loading) {
      return;
    }

    setLoading(true);

    try {
      const response = await login({
        username: username.trim(),
        password,
      });

      /* ------------------------------------------------------
         Save JWT
      ------------------------------------------------------ */

      localStorage.setItem(
        "access_token",
        response.access_token
      );

      /* ------------------------------------------------------
         Save user
      ------------------------------------------------------ */

      localStorage.setItem(
        "user",
        JSON.stringify(response.user)
      );

      /* ------------------------------------------------------
         Redirect
      ------------------------------------------------------ */

      navigate("/dashboard", {
        replace: true,
      });

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


  /* ==========================================================
     RENDER
  ========================================================== */

  return (
    <div
      className="
        min-h-screen
        flex
        min-h-screen
        items-center
        justify-center
        bg-slate-50
      "
    >

      {/* ======================================================
          LEFT BRAND PANEL
      ====================================================== */}

      <section
        className="
          hidden
        "
      >

        {/* Decorative circles */}

        <div
          className="
            absolute
            -right-24
            -top-24
            h-72
            w-72
            rounded-full
            bg-blue-500/40
          "
        />

        <div
          className="
            absolute
            -bottom-32
            -left-24
            h-96
            w-96
            rounded-full
            bg-blue-700/40
          "
        />

        <div
          className="
            absolute
            right-20
            bottom-20
            h-20
            w-20
            rounded-full
            bg-white/5
          "
        />


        <div
          className="
            relative
            z-10
            mx-auto
            w-full
            max-w-xl
          "
        >

          {/* ==================================================
              LOGO
          ================================================== */}

          <div
            className="
              mb-8
              flex
              items-center
              gap-4
            "
          >

            <div
              className="
                flex
                h-14
                w-14
                items-center
                justify-center
                rounded-2xl
                bg-white
                text-2xl
                font-black
                text-blue-600
                shadow-lg
              "
            >
              F
            </div>

            <div>

              <h1
                className="
                  text-2xl
                  font-extrabold
                  tracking-tight
                  text-white
                "
              >
                FaceAttend
              </h1>

              <p
                className="
                  mt-0.5
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wider
                  text-blue-100
                "
              >
                Attendance System
              </p>

            </div>

          </div>


          {/* ==================================================
              BRAND CONTENT
          ================================================== */}

          <div>

            <div
              className="
                mb-3
                text-sm
                font-bold
                uppercase
                tracking-[0.15em]
                text-blue-200
              "
            >
              AI-Powered Attendance
            </div>

            <h2
              className="
                max-w-lg
                text-4xl
                font-extrabold
                leading-tight
                tracking-tight
                text-white
                xl:text-5xl
              "
            >
              Smart attendance
              <br />
              with facial recognition.
            </h2>

            <p
              className="
                mt-6
                max-w-lg
                text-sm
                leading-7
                text-blue-100
                xl:text-base
              "
            >
              Manage employees and attendance
              efficiently with FaceAttend AI.
              Fast, accurate and secure.
            </p>

          </div>


          {/* ==================================================
              FEATURES
          ================================================== */}

          <div
            className="
              mt-10
              space-y-4
            "
          >

            <Feature
              title="Fast and accurate attendance"
              description="Automated attendance using facial recognition."
            />

            <Feature
              title="Real-time employee management"
              description="Manage employee information from one place."
            />

            <Feature
              title="Secure authentication"
              description="Protected access with token-based authentication."
            />

          </div>


          {/* ==================================================
              FOOTER
          ================================================== */}

          <div
            className="
              mt-12
              border-t
              border-white/10
              pt-6
              text-xs
              text-blue-200
            "
          >
            FaceAttend AI · Attendance Management
          </div>

        </div>

      </section>


      {/* ======================================================
          RIGHT LOGIN PANEL
      ====================================================== */}

      <section
        className="
          flex
          min-h-screen
          items-center
          justify-center
          px-5
          py-10
          sm:px-8
        "
      >

        <div
          className="
            w-full
            max-w-md
          "
        >

          {/* ==================================================
              MOBILE LOGO
          ================================================== */}

          <div
            className="
              mb-10
              flex
              flex-col
              items-center
              flex
            "
          >

            <div
              className="
                flex
                h-14
                w-14
                items-center
                justify-center
                rounded-2xl
                bg-blue-600
                text-2xl
                font-black
                text-white
                shadow-lg
              "
            >
              F
            </div>

            <div
              className="
                mt-3
                text-xl
                font-extrabold
                text-slate-900
              "
            >
              FaceAttend
            </div>

            <div
              className="
                mt-1
                text-[10px]
                font-bold
                uppercase
                tracking-wider
                text-slate-400
              "
            >
              Attendance System
            </div>

          </div>


          {/* ==================================================
              LOGIN CARD
          ================================================== */}

          <div
            className="
              rounded-2xl
              border
              border-slate-200
              bg-white
              p-6
              shadow-sm
              sm:p-8
            "
          >

            {/* Header */}

            <div className="mb-8">

              <h2
                className="
                  text-2xl
                  font-extrabold
                  tracking-tight
                  text-slate-900
                "
              >
                Welcome back
              </h2>

              <p
                className="
                  mt-2
                  text-sm
                  leading-6
                  text-slate-500
                "
              >
                Sign in to your FaceAttend
                account to continue.
              </p>

            </div>


            {/* =================================================
                FORM
            ================================================= */}

            <form
              onSubmit={handleSubmit}
              className="space-y-5"
            >

              {/* Username */}

              <div>

                <label
                  htmlFor="username"
                  className="
                    mb-2
                    block
                    text-sm
                    font-bold
                    text-slate-700
                  "
                >
                  Username
                </label>

                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(event) => {
                    setUsername(
                      event.target.value
                    );

                    if (error) {
                      setError("");
                    }
                  }}
                  placeholder="Enter your username"
                  autoComplete="username"
                  required
                  disabled={loading}
                  className="
                    w-full
                    rounded-xl
                    border
                    border-slate-200
                    bg-slate-50
                    px-4
                    py-3
                    text-sm
                    text-slate-800
                    outline-none
                    transition

                    placeholder:text-slate-400

                    focus:border-blue-400
                    focus:bg-white
                    focus:ring-4
                    focus:ring-blue-50

                    disabled:cursor-not-allowed
                    disabled:opacity-60
                  "
                />

              </div>


              {/* Password */}

              <div>

                <label
                  htmlFor="password"
                  className="
                    mb-2
                    block
                    text-sm
                    font-bold
                    text-slate-700
                  "
                >
                  Password
                </label>

                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => {
                    setPassword(
                      event.target.value
                    );

                    if (error) {
                      setError("");
                    }
                  }}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                  disabled={loading}
                  className="
                    w-full
                    rounded-xl
                    border
                    border-slate-200
                    bg-slate-50
                    px-4
                    py-3
                    text-sm
                    text-slate-800
                    outline-none
                    transition

                    placeholder:text-slate-400

                    focus:border-blue-400
                    focus:bg-white
                    focus:ring-4
                    focus:ring-blue-50

                    disabled:cursor-not-allowed
                    disabled:opacity-60
                  "
                />

              </div>


              {/* =================================================
                  ERROR
              ================================================= */}

              {error && (

                <div
                  role="alert"
                  className="
                    flex
                    items-start
                    gap-3
                    rounded-xl
                    border
                    border-red-200
                    bg-red-50
                    p-3.5
                  "
                >

                  <div
                    className="
                      flex
                      h-6
                      w-6
                      shrink-0
                      items-center
                      justify-center
                      rounded-full
                      bg-red-100
                      text-xs
                      font-extrabold
                      text-red-600
                    "
                  >
                    <CircleAlert size={16} strokeWidth={2} />
                  </div>

                  <p
                    className="
                      text-sm
                      leading-6
                      text-red-700
                    "
                  >
                    {error}
                  </p>

                </div>

              )}


              {/* =================================================
                  SUBMIT
              ================================================= */}

              <button
                type="submit"
                disabled={loading}
                className="
                  flex
                  w-full
                  items-center
                  justify-center
                  gap-2
                  rounded-xl
                  bg-blue-600
                  px-4
                  py-3
                  text-sm
                  font-bold
                  text-white
                  shadow-sm
                  transition

                  hover:bg-blue-700
                  hover:shadow-md

                  focus:outline-none
                  focus:ring-4
                  focus:ring-blue-100

                  disabled:cursor-not-allowed
                  disabled:opacity-60
                "
              >

                {loading && (
                  <span
                    className="
                      h-4
                      w-4
                      animate-spin
                      rounded-full
                      border-2
                      border-white/40
                      border-t-white
                    "
                  />
                )}

                {loading
                  ? "Signing in..."
                  : "Sign in"}

              </button>

            </form>


            {/* =================================================
                FOOTER
            ================================================= */}

            <div
              className="
                mt-7
                border-t
                border-slate-100
                pt-5
                text-center
                text-[11px]
                font-medium
                text-slate-400
              "
            >
              FaceAttend AI · Attendance Management
            </div>

          </div>


          {/* Security text */}

          <div
            className="
              mt-5
              flex
              items-center
              justify-center
              gap-2
              text-xs
              text-slate-400
            "
          >
            <span>
              <LockKeyhole size={14} strokeWidth={2} />
            </span>

            Secure authentication
          </div>

        </div>

      </section>

    </div>
  );
}


/* ============================================================
   FEATURE
============================================================ */

function Feature({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div
      className="
        flex
        items-start
        gap-3
      "
    >

      <div
        className="
          mt-0.5
          flex
          h-7
          w-7
          shrink-0
          items-center
          justify-center
          rounded-full
          bg-white/10
          text-xs
          font-bold
          text-white
        "
      >
        <Check size={15} strokeWidth={2.5} />
      </div>

      <div>

        <div
          className="
            text-sm
            font-bold
            text-white
          "
        >
          {title}
        </div>

        <div
          className="
            mt-1
            text-xs
            leading-5
            text-blue-200
          "
        >
          {description}
        </div>

      </div>

    </div>
  );
}