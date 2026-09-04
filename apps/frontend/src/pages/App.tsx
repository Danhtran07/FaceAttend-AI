import { useEffect, useRef, useState, type CSSProperties } from "react";

const API_BASE = import.meta.env.VITE_AI_URL || "http://localhost:8001";
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
        setError("WebSocket AI liveness không kết nối. Kiểm tra AI service tại localhost:8001.");
        cleanup();
      };
    } catch (reason) {
      cleanup();
      const message = reason instanceof Error ? reason.message : "Không xác định";
      console.error("Camera/AI startup failed:", reason);

      if (message.includes("Permission") || message.includes("NotAllowedError") || message.includes("camera")) {
        setError("Trình duyệt chưa được cấp quyền camera. Cho phép truy cập camera và thử lại.");
      } else if (message.includes("session") || message.includes("Session failed") || message.includes("AI session")) {
        setError("Không tạo được phiên xác minh trên AI service. Kiểm tra http://localhost:8001/health");
      } else if (message.includes("WebSocket") || message.includes("localhost:8001")) {
        setError("Không kết nối được AI service qua WebSocket. Kiểm tra port 8001.");
      } else {
        setError(`Không thể khởi động camera hoặc AI service. Chi tiết: ${message}`);
      }

      setFeedback("Chưa bắt đầu xác minh");
    }
  };

  const progress = challenge === "COMPLETE" ? 100 : Math.max(0, Math.min(100, (challengeIndex / CHALLENGES.length) * 100));

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <header style={styles.header}>
          <div><span style={styles.eyebrow}>FACEATTEND</span><h1>Identity Verification</h1></div>
          <span style={{ ...styles.badge, color: running ? "#5eead4" : "#94a3b8" }}>{running ? "LIVE" : "READY"}</span>
        </header>
        <div style={styles.cameraWrap}>
          <video ref={videoRef} autoPlay playsInline muted style={styles.video} />
          <div style={{ ...styles.oval, borderColor: error ? "#f87171" : challenge === "COMPLETE" ? "#34d399" : running ? "#38bdf8" : "#64748b" }} />
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>
        <section style={styles.status}>
          <strong style={{ color: error ? "#fca5a5" : token ? "#86efac" : "#e2e8f0" }}>{error || feedback}</strong>
          <div style={styles.steps}>{CHALLENGES.map((label, index) => <div key={label} style={{ ...styles.step, color: index < challengeIndex ? "#34d399" : index === challengeIndex ? "#60a5fa" : "#64748b" }}><span style={styles.dot}>{index < challengeIndex ? "OK" : index + 1}</span>{label}</div>)}</div>
          <div style={styles.track}><div style={{ ...styles.progress, width: `${progress}%` }} /></div>
        </section>
        <button onClick={running ? cleanup : start} style={styles.button}>{running ? "Dừng xác minh" : token ? "Xác minh lại" : "Bắt đầu xác minh"}</button>
        {token && <pre style={styles.token}>{token}</pre>}
        <small style={styles.endpoint}>AI service: {API_BASE}</small>
      </section>
    </main>
  );
}

const styles: Record<string, CSSProperties> = {
  page: { minHeight: "100vh", padding: 24, background: "radial-gradient(circle at top, #172554, #07090e 55%)", color: "#e2e8f0", fontFamily: "Georgia, 'Times New Roman', serif" },
  shell: { width: "min(100%, 560px)", margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 },
  eyebrow: { color: "#5eead4", letterSpacing: 3, fontSize: 11, fontWeight: 700 },
  badge: { border: "1px solid currentColor", borderRadius: 20, padding: "5px 10px", fontSize: 11, letterSpacing: 1 },
  cameraWrap: { position: "relative", aspectRatio: "4 / 3", overflow: "hidden", background: "#020617", border: "1px solid #334155", borderRadius: 14 },
  video: { width: "100%", height: "100%", objectFit: "cover", transform: "scaleX(-1)" },
  oval: { position: "absolute", inset: "14% 28%", border: "3px solid", borderRadius: "50%", boxShadow: "0 0 30px rgba(56,189,248,.15)" },
  status: { marginTop: 16, padding: 18, background: "rgba(15,23,42,.8)", border: "1px solid #1e293b", borderRadius: 14, textAlign: "center" },
  steps: { display: "flex", justifyContent: "space-around", gap: 8, marginTop: 18 },
  step: { display: "grid", gap: 6, justifyItems: "center", fontSize: 12 },
  dot: { display: "grid", placeItems: "center", width: 30, height: 30, borderRadius: "50%", background: "#1e293b", fontSize: 10 },
  track: { height: 4, marginTop: 18, background: "#1e293b", borderRadius: 2, overflow: "hidden" },
  progress: { height: "100%", background: "#38bdf8", transition: "width .2s" },
  button: { width: "100%", marginTop: 16, padding: "14px 18px", border: 0, borderRadius: 10, background: "#5eead4", color: "#042f2e", fontSize: 16, fontWeight: 700, cursor: "pointer" },
  token: { marginTop: 14, padding: 14, whiteSpace: "pre-wrap", wordBreak: "break-all", color: "#86efac", background: "#052e16", border: "1px solid #166534", borderRadius: 10, fontSize: 11 },
  endpoint: { display: "block", marginTop: 14, color: "#64748b", textAlign: "center", fontFamily: "monospace" },
};
