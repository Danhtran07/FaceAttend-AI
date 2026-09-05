import { useEffect, useRef, useState, type CSSProperties } from "react";

const API_BASE = import.meta.env.VITE_AI_URL || "http://localhost:8002";
const CHALLENGES = ["Turn Left", "Turn Right"];

type ServerMessage = {
  challenge?: string;
  challenge_index?: number;
  feedback?: string;
  liveness_token?: string;
};

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<number | null>(null);
  const [running, setRunning] = useState(false);
  const [feedback, setFeedback] = useState("Nhấn bắt đầu để kiểm tra danh tính");
  const [error, setError] = useState("");
  const [challengeIndex, setChallengeIndex] = useState(-1);
  const [challenge, setChallenge] = useState("");
  const [token, setToken] = useState("");

  const cleanup = (stopStream = true) => {
    if (timerRef.current !== null) window.clearInterval(timerRef.current);
    timerRef.current = null;
    socketRef.current?.close();
    socketRef.current = null;
    if (stopStream) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
    }
    setRunning(false);
  };

  useEffect(() => cleanup, []);

  const start = async () => {
    if (running || socketRef.current || timerRef.current !== null) return;

    setError("");
    setToken("");
    setChallengeIndex(-1);
    setChallenge("");
    setFeedback("Đang mở camera...");
    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera API không được hỗ trợ trên trình duyệt này.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (!videoRef.current) throw new Error("Video element unavailable");
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      const response = await fetch(`${API_BASE}/session/create`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`AI session creation failed (${response.status})`);
      }
      const session = await response.json();
      const socket = new WebSocket(`${API_BASE.replace(/^http/, "ws")}/ws/liveness/${session.session_id}`);
      socket.binaryType = "arraybuffer";
      socketRef.current = socket;

      const captureLoop = () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas) return;
        if (socketRef.current !== socket || socket.readyState !== WebSocket.OPEN) return;
        if (video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext("2d");
        if (!context) return;

        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (!blob || socketRef.current !== socket || socket.readyState !== WebSocket.OPEN) return;
          void blob.arrayBuffer().then((buffer) => {
            if (socketRef.current === socket && socket.readyState === WebSocket.OPEN) {
              socket.send(buffer);
            }
          }).catch(() => undefined);
        }, "image/jpeg", 0.75);
      };

      socket.onopen = () => {
        setRunning(true);
        setFeedback("Đặt khuôn mặt vào giữa khung hình...");
        timerRef.current = window.setInterval(captureLoop, 1000 / 15);
      };
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data) as ServerMessage;
        setFeedback(data.feedback || "Đang phân tích...");
        setChallengeIndex(data.challenge_index ?? -1);
        setChallenge(data.challenge || "");
        if (data.challenge === "COMPLETE") {
          setFeedback("Xác minh hoàn tất");
          setToken(data.liveness_token || "");
          cleanup();
        } else if (data.challenge === "FAILED") {
          setError(data.feedback || "Xác minh thất bại");
          cleanup(false);
        }
      };
      socket.onerror = () => {
        setError("WebSocket AI liveness không kết nối. Kiểm tra AI service tại localhost:8002.");
        cleanup();
      };
    } catch (reason) {
      cleanup();
      const message = reason instanceof Error ? reason.message : "Không xác định";
      console.error("Camera/AI startup failed:", reason);

      if (message.includes("Permission") || message.includes("NotAllowedError") || message.includes("camera")) {
        setError("Trình duyệt chưa được cấp quyền camera. Cho phép truy cập camera và thử lại.");
      } else if (message.includes("session") || message.includes("Session failed") || message.includes("AI session")) {
        setError("Không tạo được phiên xác minh trên AI service. Kiểm tra http://localhost:8002/health");
      } else if (message.includes("WebSocket") || message.includes("localhost:8002")) {
        setError("Không kết nối được AI service qua WebSocket. Kiểm tra port 8002.");
      } else {
        setError(`Không thể khởi động camera hoặc AI service. Chi tiết: ${message}`);
      }

      setFeedback("Chưa bắt đầu xác minh");
    }
  };

  const progress = challenge === "COMPLETE" ? 100 : Math.max(0, Math.min(100, (challengeIndex / CHALLENGES.length) * 100));
  const stateLabel = error ? "REVIEW REQUIRED" : token ? "VERIFIED" : running ? "LIVE CHECK" : "READY";

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <header style={styles.header}>
          <div>
            <span style={styles.eyebrow}>FACEATTEND / ATTENDANCE CONSOLE</span>
            <h1 style={styles.title}>Verify attendance</h1>
            <p style={styles.subtitle}>Live identity check before creating an attendance record.</p>
          </div>
          <span style={{ ...styles.badge, color: error ? "#dc2626" : token ? "#16a34a" : running ? "#2563eb" : "#64748b" }}>{stateLabel}</span>
        </header>
        <div style={styles.workspace}>
          <section style={styles.primaryPanel}>
            <div style={styles.panelBar}>
              <div><span style={styles.sectionKicker}>BIOMETRIC INPUT</span><h2 style={styles.panelTitle}>Camera verification</h2></div>
              <span style={styles.sessionTag}>{running ? "SESSION ACTIVE" : "SESSION IDLE"}</span>
            </div>
            <div style={styles.cameraWrap}>
              <video ref={videoRef} autoPlay playsInline muted style={styles.video} />
              <div style={{ ...styles.oval, borderColor: error ? "#ef4444" : challenge === "COMPLETE" ? "#22c55e" : running ? "#60a5fa" : "#94a3b8" }} />
              <div style={styles.cameraHint}>{running ? "Keep your face inside the frame" : "Camera preview"}</div>
              <canvas ref={canvasRef} style={{ display: "none" }} />
            </div>
            <section style={styles.status}>
              <span style={styles.sectionKicker}>CURRENT INSTRUCTION</span>
              <strong style={{ ...styles.feedback, color: error ? "#dc2626" : token ? "#16a34a" : "#0f172a" }}>{error || feedback}</strong>
              <div style={styles.steps}>{CHALLENGES.map((label, index) => <div key={label} style={{ ...styles.step, color: index < challengeIndex ? "#16a34a" : index === challengeIndex ? "#2563eb" : "#64748b" }}><span style={{ ...styles.dot, borderColor: index < challengeIndex ? "#22c55e" : index === challengeIndex ? "#60a5fa" : "#cbd5e1" }}>{index < challengeIndex ? "DONE" : `0${index + 1}`}</span>{label}</div>)}</div>
              <div style={styles.track}><div style={{ ...styles.progress, width: `${progress}%` }} /></div>
            </section>
            <button onClick={running ? cleanup : start} style={styles.button}>{running ? "Stop verification" : token ? "Run again" : "Start verification"}</button>
            {token && <pre style={styles.token}>{token}</pre>}
          </section>

          <aside style={styles.rail}>
            <div style={styles.railSection}>
              <span style={styles.sectionKicker}>RECORD CONTEXT</span>
              <div style={styles.recordRow}><span>Employee</span><strong>Pending match</strong></div>
              <div style={styles.recordRow}><span>Employee ID</span><strong>Not assigned</strong></div>
              <div style={styles.recordRow}><span>Attendance state</span><strong>{token ? "Ready to record" : "Awaiting verification"}</strong></div>
            </div>
            <div style={styles.railSection}>
              <span style={styles.sectionKicker}>VERIFICATION SESSION</span>
              <div style={styles.recordRow}><span>Method</span><strong>Face liveness</strong></div>
              <div style={styles.recordRow}><span>Required checks</span><strong>2 gestures</strong></div>
              <div style={styles.recordRow}><span>Service</span><strong>AI / 8002</strong></div>
            </div>
            <div style={styles.notice}><span style={styles.sectionKicker}>NEXT STEP</span><p>{token ? "Identity verified. The attendance event can now be persisted." : "Complete both head-turn checks to continue."}</p></div>
            <small style={styles.endpoint}>AI service: {API_BASE}</small>
          </aside>
        </div>
      </section>
    </main>
  );
}

const styles: Record<string, CSSProperties> = {
  page: { minHeight: "100vh", padding: "clamp(20px, 4vw, 56px)", background: "#f8fafc", color: "#0f172a", fontFamily: "'Space Grotesk', 'Trebuchet MS', sans-serif" },
  shell: { width: "min(100%, 1180px)", margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 24, marginBottom: 28 },
  eyebrow: { color: "#2563eb", letterSpacing: 2.4, fontSize: 10, fontWeight: 700 },
  title: { margin: "8px 0 4px", fontSize: "clamp(28px, 4vw, 46px)", lineHeight: 1.05, letterSpacing: -1, color: "#0f172a" },
  subtitle: { margin: 0, color: "#64748b", fontSize: 14 },
  badge: { border: "1px solid currentColor", borderRadius: 999, padding: "8px 12px", fontSize: 10, letterSpacing: 1.2, fontWeight: 700, whiteSpace: "nowrap" },
  workspace: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: 16, alignItems: "start" },
  primaryPanel: { padding: 18, background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 18, boxShadow: "0 4px 16px rgba(15, 23, 42, .05)" },
  panelBar: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: 14 },
  sectionKicker: { display: "block", color: "#64748b", fontSize: 10, letterSpacing: 1.5, fontWeight: 700 },
  panelTitle: { margin: "5px 0 0", fontSize: 20, fontWeight: 600, color: "#0f172a" },
  sessionTag: { color: "#64748b", fontSize: 10, letterSpacing: 1, paddingTop: 5 },
  cameraWrap: { position: "relative", aspectRatio: "16 / 10", overflow: "hidden", background: "#0f172a", border: "1px solid #cbd5e1", borderRadius: 12 },
  video: { width: "100%", height: "100%", objectFit: "cover", transform: "scaleX(-1)" },
  oval: { position: "absolute", inset: "12% 35%", border: "2px solid", borderRadius: "50%", boxShadow: "0 0 0 999px rgba(15, 23, 42, .12)" },
  cameraHint: { position: "absolute", bottom: 12, left: 16, color: "#d4d4d8", fontSize: 11, background: "rgba(9,9,11,.72)", padding: "6px 8px", borderRadius: 5 },
  status: { marginTop: 14, padding: "16px 4px 2px", textAlign: "left" },
  feedback: { display: "block", marginTop: 7, fontSize: 18, fontWeight: 600 },
  steps: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 20 },
  step: { display: "flex", alignItems: "center", gap: 9, fontSize: 13 },
  dot: { display: "grid", placeItems: "center", width: 42, height: 26, border: "1px solid", borderRadius: 5, background: "#f8fafc", fontSize: 9, fontWeight: 700, letterSpacing: .8 },
  track: { height: 4, marginTop: 18, background: "#e2e8f0", borderRadius: 2, overflow: "hidden" },
  progress: { height: "100%", background: "#2563eb", transition: "width .2s" },
  button: { width: "100%", marginTop: 20, padding: "13px 18px", border: "1px solid #2563eb", borderRadius: 7, background: "#2563eb", color: "#ffffff", fontSize: 14, fontWeight: 700, cursor: "pointer" },
  token: { marginTop: 14, padding: 14, whiteSpace: "pre-wrap", wordBreak: "break-all", color: "#166534", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, fontSize: 11 },
  rail: { background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 18, overflow: "hidden", boxShadow: "0 4px 16px rgba(15, 23, 42, .05)" },
  railSection: { padding: 18, borderBottom: "1px solid #e2e8f0" },
  recordRow: { display: "flex", justifyContent: "space-between", gap: 12, padding: "13px 0", borderBottom: "1px solid #f1f5f9", fontSize: 12, color: "#64748b" },
  notice: { margin: 14, padding: 14, background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: 8, color: "#1e3a8a" },
  endpoint: { display: "block", margin: "0 18px 18px", color: "#94a3b8", fontSize: 10, fontFamily: "monospace" },
};
