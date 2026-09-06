import { useEffect, useState } from "react";

import { getApiErrorMessage } from "../api/error";
import { getProfile, updateProfile, uploadProfileAvatar } from "../api/auth.api";
import LoadingState from "../components/LoadingState";
import ErrorState from "../components/ErrorState";
import type { Profile as ProfileData, ProfileUpdate } from "../types/user";

const emptyForm: ProfileUpdate = { full_name: "", email: "", phone: "", avatar_url: "", bio: "" };
const apiOrigin = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function Profile() {
  const storedUser = (() => {
    try { return JSON.parse(localStorage.getItem("user") || "{}"); } catch { return {}; }
  })();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [form, setForm] = useState<ProfileUpdate>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadProfile() {
    try {
      setLoading(true); setError("");
      const data = await getProfile();
      setProfile(data);
      setForm({ full_name: data.full_name || "", email: data.email || "", phone: data.phone || "", avatar_url: data.avatar_url || "", bio: data.bio || "" });
    } catch (err) { setError(getApiErrorMessage(err, "Unable to load your profile.")); } finally { setLoading(false); }
  }

  useEffect(() => { void loadProfile(); }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try { setSaving(true); setError(""); setSuccess(""); const data = await updateProfile(form); setProfile(data); setSuccess("Profile updated successfully."); } catch (err) { setError(getApiErrorMessage(err, "Unable to update your profile.")); } finally { setSaving(false); }
  }

  async function handleAvatar(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try { setUploading(true); setError(""); const data = await uploadProfileAvatar(file); setProfile(data); setForm((current) => ({ ...current, avatar_url: data.avatar_url || "" })); setSuccess("Avatar updated successfully."); } catch (err) { setError(getApiErrorMessage(err, "Unable to upload avatar.")); } finally { setUploading(false); event.target.value = ""; }
  }

  if (loading) return <LoadingState message="Loading profile..." />;
  if (error && !profile) return <ErrorState message={error} onRetry={() => void loadProfile()} />;

  const avatar = profile?.avatar_url ? `${apiOrigin}${profile.avatar_url}` : "";
  return <section className="mx-auto max-w-4xl space-y-6">
    <header><p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-600">Account</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">My profile</h1><p className="mt-1 text-sm text-slate-500">{storedUser.username || "User"} · {storedUser.role || "EMPLOYEE"}</p></header>
    {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
    {success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{success}</div>}
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <aside className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm"><div className="mx-auto flex h-28 w-28 items-center justify-center overflow-hidden rounded-full bg-blue-100 text-4xl font-bold text-blue-600">{avatar ? <img src={avatar} alt="Profile avatar" className="h-full w-full object-cover" /> : (profile?.full_name || storedUser.username || "U").charAt(0).toUpperCase()}</div><h2 className="mt-4 truncate text-lg font-bold text-slate-900">{profile?.full_name || storedUser.username || "User"}</h2><p className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-400">{storedUser.role || "EMPLOYEE"}</p><label className="mt-5 inline-flex cursor-pointer rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"><input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleAvatar} disabled={uploading} className="sr-only" />{uploading ? "Uploading..." : "Change photo"}</label><p className="mt-3 text-xs text-slate-400">JPG, PNG or WebP up to 5 MB</p></aside>
      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="grid gap-5 sm:grid-cols-2"><label className="sm:col-span-2"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Full name</span><input value={form.full_name || ""} onChange={(event) => setForm({ ...form, full_name: event.target.value })} maxLength={100} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" /></label><label><span className="mb-1.5 block text-sm font-semibold text-slate-700">Email</span><input type="email" value={form.email || ""} onChange={(event) => setForm({ ...form, email: event.target.value })} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" /></label><label><span className="mb-1.5 block text-sm font-semibold text-slate-700">Phone</span><input value={form.phone || ""} onChange={(event) => setForm({ ...form, phone: event.target.value })} maxLength={30} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" /></label><label className="sm:col-span-2"><span className="mb-1.5 block text-sm font-semibold text-slate-700">Bio</span><textarea rows={5} value={form.bio || ""} onChange={(event) => setForm({ ...form, bio: event.target.value })} className="w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" /></label></div><div className="mt-6 flex justify-end"><button type="submit" disabled={saving} className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50">{saving ? "Saving..." : "Save changes"}</button></div></form>
    </div>
  </section>;
}