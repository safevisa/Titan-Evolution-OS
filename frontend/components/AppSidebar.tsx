"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import { useAuth } from "@/hooks/useAuth";

const C = {
  surface: "#0d1017",
  surfaceHigh: "#13171f",
  border: "rgba(255,255,255,0.06)",
  text: "#e8eaf0",
  textMid: "#8892a4",
  textDim: "#3d4557",
  accent: "#5b6ef5",
  green: "#2dd4a0",
  purple: "#a78bfa",
};

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "⬡" },
  { id: "agents", label: "Digital Team", icon: "◈" },
  { id: "tasks", label: "Task Center", icon: "⊞" },
  { id: "evolution", label: "Evolution", icon: "◎" },
  { id: "skills", label: "Skills Library", icon: "⟐" },
  { id: "billing", label: "Billing", icon: "◇" },
  { id: "settings", label: "Settings", icon: "⊛" },
];

const NAV_ADMIN = { id: "admin", label: "Admin", icon: "⚙" };

export type SidebarLabels = {
  dashboard: string;
  agents: string;
  tasks: string;
  evolution: string;
  skills: string;
  billing: string;
  settings: string;
  admin?: string;
};

export function AppSidebar({ locale, labels }: { locale: string; labels?: SidebarLabels }) {
  const pathname = usePathname();
  const { user, plan, isPlatformAdmin } = useAuth();

  const initials = user?.name
    ? user.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() ?? "?";

  const localizedLabel = (id: string) => {
    if (!labels) return NAV.find(n => n.id === id)?.label ?? NAV_ADMIN.label;
    return (labels as Record<string, string>)[id] ?? NAV.find(n => n.id === id)?.label ?? NAV_ADMIN.label;
  };

  const navItems = isPlatformAdmin ? [...NAV, NAV_ADMIN] : NAV;

  return (
    <div style={{ width: 220, flexShrink: 0, background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", height: "100vh", position: "sticky", top: 0 }}>
      {/* Logo */}
      <div style={{ padding: "24px 20px 20px", borderBottom: `1px solid ${C.border}` }}>
        <Link href={`/${locale}/dashboard`} style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, flexShrink: 0 }}>⚡</div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, letterSpacing: "0.06em" }}>TITAN</div>
            <div style={{ fontSize: 10, color: C.textDim, letterSpacing: "0.12em" }}>EVOLUTION OS</div>
          </div>
        </Link>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "12px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
        {navItems.map(n => {
          const href = `/${locale}/${n.id}`;
          const isActive = pathname.includes(`/${n.id}`);
          return (
            <Link key={n.id} href={href} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", borderRadius: 8, textDecoration: "none", background: isActive ? `${C.accent}18` : "transparent", color: isActive ? C.accent : C.textMid, fontSize: 13, fontWeight: isActive ? 600 : 400, borderLeft: `2px solid ${isActive ? C.accent : "transparent"}`, transition: "all 0.15s" }}>
              <span style={{ fontSize: 15, width: 18, textAlign: "center" }}>{n.icon}</span>
              {localizedLabel(n.id)}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div style={{ padding: 16, borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: "50%", background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, color: "#fff", fontWeight: 700, flexShrink: 0 }}>
            {user?.image
            // eslint-disable-next-line @next/next/no-img-element
            ? <img src={user.image} alt="" style={{ width: 32, height: 32, borderRadius: "50%" }} />
            : initials}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, color: C.text, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{user?.name ?? user?.email ?? "User"}</div>
            <div style={{ fontSize: 11, color: C.textDim }}>
              {isPlatformAdmin ? "platform admin" : `${plan} plan`}
            </div>
          </div>
        </div>
        <button onClick={() => signOut({ callbackUrl: "/login" })} style={{ width: "100%", padding: "7px", borderRadius: 7, border: `1px solid ${C.border}`, background: "transparent", color: C.textMid, fontSize: 12, cursor: "pointer", transition: "all 0.15s" }}
          onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
          onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
          Sign out
        </button>
      </div>
    </div>
  );
}
