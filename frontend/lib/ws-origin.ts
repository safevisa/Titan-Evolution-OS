/** WebSocket origin for task live logs (matches API host). */
export function wsOrigin(): string {
  const api = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (api) {
    try {
      const u = new URL(api.replace(/\/api\/v1\/?$/, ""));
      u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
      return u.origin;
    } catch {
      /* fall through */
    }
  }
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.host}`;
  }
  return "ws://127.0.0.1:8000";
}

export function taskLogWsUrl(taskId: string): string {
  return `${wsOrigin()}/ws/tasks/${taskId}`;
}
