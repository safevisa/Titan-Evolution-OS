"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

const C = {
  bg: "#07090f", surface: "#0d1017", surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)", text: "#e8eaf0", textMid: "#8892a4",
  textDim: "#3d4557", accent: "#5b6ef5", accentGlow: "rgba(91,110,245,0.2)",
  purple: "#a78bfa",
};

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/en/dashboard";

  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    setError(""); setLoading(true);
    try {
      if (tab === "register") {
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password }),
        });
        const data = await res.json();
        if (!res.ok) { setError(data.error ?? "Registration failed"); setLoading(false); return; }
      }
      const result = await signIn("credentials", { email, password, redirect: false });
      if (result?.error) { setError("Invalid email or password"); setLoading(false); return; }
      router.push(callbackUrl);
    } catch { setError("Something went wrong"); setLoading(false); }
  }

  async function handleGoogle() {
    setError("");
    setLoading(true);
    try {
      // SessionProvider is required (see root layout); redirect sends user to Google OAuth.
      await signIn("google", { callbackUrl, redirect: true });
    } catch {
      setError("Google sign-in could not start. Try again or use email sign-in.");
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: C.bg, display: "flex", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden", fontFamily: "'DM Sans','Helvetica Neue',sans-serif" }}>
      <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');`}</style>
      <div style={{ position: "absolute", width: 600, height: 600, borderRadius: "50%", background: `radial-gradient(circle, ${C.accentGlow} 0%, transparent 70%)`, top: "50%", left: "50%", transform: "translate(-50%,-50%)", pointerEvents: "none" }} />

      <div style={{ width: 420, position: "relative", zIndex: 1 }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ width: 52, height: 52, borderRadius: 14, background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, margin: "0 auto 16px", boxShadow: `0 8px 32px ${C.accentGlow}` }}>⚡</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: C.text, letterSpacing: "0.05em" }}>Titan Evolution OS</div>
          <div style={{ fontSize: 13, color: C.textMid, marginTop: 6 }}>Self-evolving digital workforce OS</div>
        </div>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 32 }}>
          <div style={{ display: "flex", marginBottom: 28, background: C.surfaceHigh, borderRadius: 9, padding: 3 }}>
            {(["login", "register"] as const).map(t => (
              <button key={t} onClick={() => { setTab(t); setError(""); }} style={{ flex: 1, padding: "8px", borderRadius: 7, border: "none", cursor: "pointer", background: tab === t ? C.surface : "transparent", color: tab === t ? C.text : C.textMid, fontSize: 13, fontWeight: tab === t ? 600 : 400, boxShadow: tab === t ? "0 1px 4px rgba(0,0,0,0.4)" : "none", transition: "all 0.18s" }}>
                {t === "login" ? "Sign In" : "Register"}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {tab === "register" && (
              <div>
                <label style={{ display: "block", fontSize: 12, color: C.textMid, marginBottom: 6 }}>Name</label>
                <input placeholder="Your name" value={name} onChange={e => setName(e.target.value)} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }} onFocus={e => e.target.style.borderColor = C.accent} onBlur={e => e.target.style.borderColor = C.border} />
              </div>
            )}
            <div>
              <label style={{ display: "block", fontSize: 12, color: C.textMid, marginBottom: 6 }}>Email</label>
              <input type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }} onFocus={e => e.target.style.borderColor = C.accent} onBlur={e => e.target.style.borderColor = C.border} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: 12, color: C.textMid, marginBottom: 6 }}>Password</label>
              <input type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSubmit()} style={{ width: "100%", padding: "11px 14px", background: C.surfaceHigh, border: `1px solid ${C.border}`, borderRadius: 9, color: C.text, fontSize: 14, outline: "none" }} onFocus={e => e.target.style.borderColor = C.accent} onBlur={e => e.target.style.borderColor = C.border} />
            </div>

            {error && <p style={{ fontSize: 13, color: "#f25f5c", margin: 0 }}>{error}</p>}

            <button onClick={handleSubmit} disabled={loading} style={{ width: "100%", padding: "13px", borderRadius: 9, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 15, background: loading ? "#3d4557" : C.accent, color: "#fff", marginTop: 4 }}>
              {loading ? "Please wait..." : tab === "login" ? "Sign In" : "Create Account"}
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ flex: 1, height: 1, background: C.border }} />
              <span style={{ fontSize: 12, color: C.textDim }}>or</span>
              <div style={{ flex: 1, height: 1, background: C.border }} />
            </div>

            <button onClick={handleGoogle} disabled={loading} style={{ width: "100%", padding: "11px", borderRadius: 9, border: `1px solid ${C.border}`, background: C.surfaceHigh, color: C.text, fontSize: 13, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 10, fontWeight: 500 }}>
              <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
              Continue with Google
            </button>
          </div>
        </div>
        <p style={{ textAlign: "center", marginTop: 20, fontSize: 12, color: C.textDim }}>
          By signing in you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
}
