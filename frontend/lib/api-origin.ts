/**
 * Browser API base: empty → same-origin paths `/api/v1/...` (Nginx → FastAPI).
 * Set NEXT_PUBLIC_API_URL only for local dev (e.g. http://127.0.0.1:8000).
 */
export function getApiOrigin(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();
  if (!raw) return "";
  return raw.replace(/\/$/, "");
}

/** Path must start with `/`, e.g. `/api/v1/tenants`. */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  const origin = getApiOrigin();
  if (!origin) return p;
  return `${origin}${p}`;
}
