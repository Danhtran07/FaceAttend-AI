import React, { useCallback, useEffect, useRef, useState } from "react";

type Mode = "home" | "register" | "checkin";

type RegisteredEmployee = {
  employee_id: number;
  employee_code: string;
  name: string;
  embedding: number[];
};

type UiResult = {
  ok: boolean;
  title: string;
  message: string;
};

const STORAGE_KEY = "faceattend_demo_employees";

function loadEmployees(): RegisteredEmployee[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveEmployees(employees: RegisteredEmployee[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(employees));
}

function captureBase64(video: HTMLVideoElement): string {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Không tạo được canvas");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.92).split(",")[1] ?? "";
}

function parseEmployeeId(code: string): number {
  const trimmed = code.trim();
  const asNumber = Number(trimmed);
  if (Number.isInteger(asNumber) && asNumber > 0) return asNumber;

  let hash = 0;
  for (let i = 0; i < trimmed.length; i += 1) {
    hash = (hash * 31 + trimmed.charCodeAt(i)) >>> 0;
  }
  return hash || 1;
}

export default function App() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [mode, setMode] = useState<Mode>("home");
  const [employees, setEmployees] = useState<RegisteredEmployee[]>(() => loadEmployees());
  const [name, setName] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UiResult | null>(null);
  const [cameraReady, setCameraReady] = useState(false);

  const aiBaseUrl = import.meta.env.VITE_AI_URL || "http://localhost:8001";

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraReady(false);
  }, []);

  const startCamera = useCallback(async () => {
    stopCamera();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraReady(true);
    } catch {
      setCameraReady(false);
      setResult({
        ok: false,
        title: "Không thành công",
        message: "Không mở được camera. Hãy cấp quyền camera cho trình duyệt.",
      });
    }
  }, [stopCamera]);

  useEffect(() => {
    if (mode === "register" || mode === "checkin") {
      void startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [mode, startCamera, stopCamera]);

  const goHome = () => {
    setMode("home");
    setResult(null);
    setLoading(false);
  };

  const openRegister = () => {
    setResult(null);
    setName("");
    setEmployeeCode("");
    setMode("register");
  };

  const openCheckin = () => {
    setResult(null);
    setMode("checkin");
  };

  const registerEmployee = async () => {
    if (!name.trim() || !employeeCode.trim()) {
      setResult({
        ok: false,
        title: "Không thành công",
        message: "Vui lòng nhập họ tên và mã nhân viên.",
      });
      return;
    }
    if (!videoRef.current || !cameraReady) {
      setResult({ ok: false, title: "Không thành công", message: "Camera chưa sẵn sàng." });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const image = captureBase64(videoRef.current);
      const res = await fetch(`${aiBaseUrl}/face/enroll`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image }),
      });
      const data = await res.json();

      if (!res.ok || data?.success !== true || !Array.isArray(data?.embedding)) {
        const detail =
          data?.message || data?.error?.message || data?.error_code || "UNKNOWN_ERROR";
        setResult({
          ok: false,
          title: "Không thành công",
          message: `Đăng ký thất bại: ${detail}`,
        });
        return;
      }

      const employee_id = parseEmployeeId(employeeCode);
      const next = [
        ...employees.filter((item) => item.employee_id !== employee_id),
        {
          employee_id,
          employee_code: employeeCode.trim(),
          name: name.trim(),
          embedding: data.embedding as number[],
        },
      ];
      saveEmployees(next);
      setEmployees(next);
      setResult({
        ok: true,
        title: "Thành công",
        message: `Đã đăng ký ${name.trim()} (${employeeCode.trim()}). Quay lại để điểm danh.`,
      });
    } catch {
      setResult({
        ok: false,
        title: "Không thành công",
        message: "Lỗi kết nối AI Service. Hãy chắc AI đang chạy ở cổng 8001.",
      });
    } finally {
      setLoading(false);
    }
  };

  const checkin = async () => {
    if (!videoRef.current || !cameraReady) {
      setResult({ ok: false, title: "Không thành công", message: "Camera chưa sẵn sàng." });
      return;
    }
    if (employees.length === 0) {
      setResult({
        ok: false,
        title: "Không thành công",
        message: "Chưa có nhân viên đăng ký. Hãy đăng ký trước.",
      });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const image = captureBase64(videoRef.current);
      const candidates = employees.map((item) => ({
        employee_id: item.employee_id,
        embedding: item.embedding,
      }));

      const res = await fetch(`${aiBaseUrl}/face/recognize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image, candidates, threshold: 0.5 }),
      });
      const data = await res.json();

      if (res.ok && data?.recognized === true) {
        const matched = employees.find((item) => item.employee_id === data.employee_id);
        setResult({
          ok: true,
          title: "Thành công",
          message: matched
            ? `Điểm danh thành công: ${matched.name} (${matched.employee_code}) · độ tin cậy ${(Number(data.confidence) * 100).toFixed(1)}%`
            : `Điểm danh thành công · employee_id=${data.employee_id}`,
        });
        return;
      }

      const code = data?.error_code || "UNKNOWN_FACE";
      setResult({
        ok: false,
        title: "Không thành công",
        message:
          code === "UNKNOWN_FACE"
            ? "Khuôn mặt không khớp với nhân viên đã đăng ký."
            : `Điểm danh thất bại: ${data?.message || code}`,
      });
    } catch {
      setResult({
        ok: false,
        title: "Không thành công",
        message: "Lỗi kết nối AI Service. Hãy chắc AI đang chạy ở cổng 8001.",
      });
    } finally {
      setLoading(false);
    }
  };

  const clearRegistry = () => {
    saveEmployees([]);
    setEmployees([]);
    setResult({
      ok: true,
      title: "Thành công",
      message: "Đã xóa danh sách nhân viên demo (localStorage).",
    });
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(160deg, #0f172a 0%, #1e293b 45%, #0ea5e9 160%)",
        color: "#e2e8f0",
        fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
        padding: 24,
      }}
    >
      <div style={{ maxWidth: 820, margin: "0 auto" }}>
        <header style={{ marginBottom: 20 }}>
          <h1 style={{ margin: 0, fontSize: 32, letterSpacing: 0.5 }}>FaceAttend Demo</h1>
          <p style={{ margin: "8px 0 0", opacity: 0.85 }}>
            Demo chỉ dùng AI Service · dữ liệu đăng ký lưu tạm trên trình duyệt
          </p>
          <p style={{ margin: "4px 0 0", fontSize: 13, opacity: 0.7 }}>AI: {aiBaseUrl}</p>
        </header>

        {mode === "home" && (
          <div
            style={{
              background: "rgba(15,23,42,0.72)",
              border: "1px solid rgba(148,163,184,0.25)",
              borderRadius: 16,
              padding: 28,
            }}
          >
            <p style={{ marginTop: 0 }}>
              Đã đăng ký: <strong>{employees.length}</strong> nhân viên
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <button onClick={openCheckin} style={primaryBtn}>
                Điểm danh
              </button>
              <button onClick={openRegister} style={secondaryBtn}>
                Đăng ký
              </button>
              <button onClick={clearRegistry} style={ghostBtn}>
                Xóa danh sách demo
              </button>
            </div>

            {employees.length > 0 && (
              <ul style={{ marginTop: 20, paddingLeft: 18 }}>
                {employees.map((item) => (
                  <li key={item.employee_id}>
                    {item.name} — {item.employee_code}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {(mode === "register" || mode === "checkin") && (
          <div
            style={{
              background: "rgba(15,23,42,0.72)",
              border: "1px solid rgba(148,163,184,0.25)",
              borderRadius: 16,
              padding: 20,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
              <h2 style={{ margin: 0 }}>{mode === "register" ? "Đăng ký nhân viên" : "Điểm danh"}</h2>
              <button onClick={goHome} style={ghostBtn}>
                Quay lại
              </button>
            </div>

            <div
              style={{
                marginTop: 16,
                borderRadius: 12,
                overflow: "hidden",
                border: "1px solid rgba(148,163,184,0.35)",
                background: "#000",
              }}
            >
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ width: "100%", display: "block", maxHeight: 420, objectFit: "cover" }}
              />
            </div>

            {mode === "register" && (
              <div style={{ marginTop: 16, display: "grid", gap: 10 }}>
                <label style={labelStyle}>
                  Họ tên
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Nguyễn Văn A"
                    style={inputStyle}
                  />
                </label>
                <label style={labelStyle}>
                  Mã nhân viên
                  <input
                    value={employeeCode}
                    onChange={(e) => setEmployeeCode(e.target.value)}
                    placeholder="NV001 hoặc 123"
                    style={inputStyle}
                  />
                </label>
                <button onClick={registerEmployee} disabled={loading} style={primaryBtn}>
                  {loading ? "Đang đăng ký..." : "Đăng ký"}
                </button>
              </div>
            )}

            {mode === "checkin" && (
              <div style={{ marginTop: 16 }}>
                <p style={{ opacity: 0.85 }}>
                  Nhìn vào camera rồi bấm <strong>Điểm danh</strong>. Hệ thống sẽ tự quét và so với khuôn mặt đã đăng ký.
                </p>
                <button onClick={checkin} disabled={loading} style={primaryBtn}>
                  {loading ? "Đang nhận diện..." : "Điểm danh"}
                </button>
              </div>
            )}
          </div>
        )}

        {result && (
          <div
            style={{
              marginTop: 16,
              padding: 14,
              borderRadius: 12,
              border: `1px solid ${result.ok ? "#86efac" : "#fca5a5"}`,
              background: result.ok ? "rgba(22,101,52,0.35)" : "rgba(127,29,29,0.4)",
              color: result.ok ? "#dcfce7" : "#fee2e2",
            }}
          >
            <strong style={{ fontSize: 18 }}>{result.title}</strong>
            <div style={{ marginTop: 6 }}>{result.message}</div>
          </div>
        )}
      </div>
    </div>
  );
}

const primaryBtn: React.CSSProperties = {
  padding: "12px 18px",
  borderRadius: 10,
  border: "none",
  background: "#38bdf8",
  color: "#0f172a",
  fontWeight: 700,
  cursor: "pointer",
  fontSize: 16,
};

const secondaryBtn: React.CSSProperties = {
  ...primaryBtn,
  background: "#22c55e",
};

const ghostBtn: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid rgba(148,163,184,0.45)",
  background: "transparent",
  color: "#e2e8f0",
  cursor: "pointer",
};

const labelStyle: React.CSSProperties = {
  display: "grid",
  gap: 6,
  fontSize: 14,
};

const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid rgba(148,163,184,0.45)",
  background: "#0f172a",
  color: "#e2e8f0",
  fontSize: 15,
};
