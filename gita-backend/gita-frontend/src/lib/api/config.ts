/**
 * Public API base for browser fetches.
 *
 * - If `NEXT_PUBLIC_API_BASE_URL` is set → use it, **except** in the browser when it points at
 *   loopback (127.0.0.1 / localhost) but the page is opened from another host (e.g. `http://10.x:3000`).
 *   Then we use same-origin `/api/backend` so the Next proxy hits the real API (avoids broken LAN).
 * - If unset/empty → same-origin `/api/backend`. Set `BACKEND_URL` for the Next server (see `make dev`).
 *
 * When `NEXT_PUBLIC_API_BASE_URL` is unset, the resolved base differs on server vs browser
 * (origin is only known in the client). Do not render this string during SSR unless you
 * gate on `useEffect` / `typeof window` after hydration (see `StatusPanel`).
 */
function _isLoopbackHost(hostname: string): boolean {
  const h = hostname.toLowerCase();
  return h === "localhost" || h === "127.0.0.1" || h === "::1" || h === "[::1]";
}

export function getPublicApiBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (explicit && typeof window !== "undefined") {
    try {
      const api = new URL(explicit);
      const pageHost = window.location.hostname;
      if (_isLoopbackHost(api.hostname) && !_isLoopbackHost(pageHost)) {
        return `${window.location.origin}/api/backend`.replace(/\/$/, "");
      }
    } catch {
      /* use explicit below */
    }
  }
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    return `${window.location.origin}/api/backend`;
  }
  return (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
}

/** Label for the dev status panel */
export function getConfiguredApiLabel(): string {
  if (typeof window !== "undefined") {
    return getPublicApiBaseUrl();
  }
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (explicit) return explicit.replace(/\/$/, "");
  return "same-origin /api/backend → " + (process.env.BACKEND_URL ?? "http://127.0.0.1:8000");
}
