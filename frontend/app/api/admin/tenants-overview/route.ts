import { NextResponse } from "next/server";
import { auth } from "@/auth";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id || session.user.role !== "platform_admin") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
  const key = (process.env.TITAN_ADMIN_API_KEY ?? "").trim();
  if (!key) {
    return NextResponse.json(
      { error: "TITAN_ADMIN_API_KEY is not set on the Next.js server" },
      { status: 503 }
    );
  }
  const backend = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  const res = await fetch(`${backend}/api/v1/admin/tenants-overview`, {
    headers: { "X-Titan-Admin-Key": key },
  });
  const data = await res.json().catch(() => []);
  return NextResponse.json(data, { status: res.status });
}
