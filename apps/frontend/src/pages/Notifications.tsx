import { useEffect, useState } from "react";
import { Bell, Check, CircleAlert, Clock3, ExternalLink, Info, TriangleAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getNotifications, markNotificationRead } from "../api/notifications.api";
import type { Notification, NotificationSeverity } from "../types/notification";

const severityStyles: Record<NotificationSeverity, { icon: typeof Info; iconClass: string; borderClass: string }> = {
  info: { icon: Info, iconClass: "bg-blue-50 text-blue-600", borderClass: "border-blue-100" },
  warning: { icon: TriangleAlert, iconClass: "bg-amber-50 text-amber-600", borderClass: "border-amber-100" },
  urgent: { icon: CircleAlert, iconClass: "bg-red-50 text-red-600", borderClass: "border-red-100" },
  success: { icon: Check, iconClass: "bg-emerald-50 text-emerald-600", borderClass: "border-emerald-100" },
};

function formatRelativeTime(value: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "Just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "Yesterday" : `${days} days ago`;
}

function groupLabel(value: string): "Today" | "Yesterday" | "Earlier" {
  const date = new Date(value);
  const now = new Date();
  const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const notificationDay = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const difference = Math.round((dayStart - notificationDay) / 86400000);
  if (difference === 0) return "Today";
  if (difference === 1) return "Yesterday";
  return "Earlier";
}

export default function Notifications() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadNotifications() {
    try {
      setError("");
      setNotifications(await getNotifications());
    } catch {
      setError("Unable to load notifications right now.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
    const timer = window.setInterval(() => void loadNotifications(), 60000);
    return () => window.clearInterval(timer);
  }, []);

  async function handleAction(notification: Notification) {
    if (!notification.is_read) {
      await markNotificationRead(notification.id);
      setNotifications((current) => current.map((item) => item.id === notification.id ? { ...item, is_read: true } : item));
    }
    if (notification.action_path) navigate(notification.action_path);
  }

  const grouped = ["Today", "Yesterday", "Earlier"].map((label) => ({
    label,
    items: notifications.filter((notification) => groupLabel(notification.created_at) === label),
  })).filter((group) => group.items.length > 0);

  return (
    <div className="mx-auto w-full max-w-4xl">
      <header className="mb-8 flex items-start justify-between gap-4">
        <div>
          <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.14em] text-blue-600">Attendance assistant</p>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Notification Center</h1>
          <p className="mt-2 text-sm text-slate-500">Timely updates about your attendance and requests.</p>
        </div>
        <div className="hidden h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 sm:flex">
          <Bell size={22} />
        </div>
      </header>

      {error && <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
      {loading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">Loading notifications...</div>
      ) : grouped.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white px-6 py-14 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600"><Check size={22} /></div>
          <h2 className="text-lg font-bold text-slate-900">You are all caught up</h2>
          <p className="mt-2 text-sm text-slate-500">There are no active attendance notifications.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {grouped.map((group) => (
            <section key={group.label}>
              <div className="mb-3 flex items-center gap-3"><h2 className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{group.label}</h2><div className="h-px flex-1 bg-slate-200" /></div>
              <div className="space-y-3">
                {group.items.map((notification) => {
                  const style = severityStyles[notification.severity];
                  const Icon = style.icon;
                  return (
                    <article key={notification.id} className={`border ${style.borderClass} rounded-2xl bg-white p-5 shadow-sm transition hover:shadow-md ${notification.is_read ? "opacity-75" : ""}`}>
                      <div className="flex gap-4">
                        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${style.iconClass}`}><Icon size={19} /></div>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-start justify-between gap-2">
                            <h3 className="font-bold text-slate-900">{notification.title}</h3>
                            <span className="whitespace-nowrap text-xs text-slate-400">{formatRelativeTime(notification.created_at)}</span>
                          </div>
                          <p className="mt-1.5 text-sm leading-6 text-slate-600">{notification.message}</p>
                          {notification.action_label && <button type="button" onClick={() => void handleAction(notification)} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3.5 py-2 text-xs font-bold text-white transition hover:bg-blue-600"><ExternalLink size={14} />{notification.action_label}</button>}
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
