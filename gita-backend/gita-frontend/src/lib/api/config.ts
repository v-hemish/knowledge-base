/**
 * Public API base for browser fetches.
 *
 * - If `NEXT_PUBLIC_API_BASE_URL` is set → use it (direct to FastAPI; requires CORS).
 * - If unset/empty → same-origin `/api/backend` proxy (see `src/app/api/backend/...`);
 *   set `BACKEND_URL` on the Next server (defaults to http://127.0.0.1:8000).
 *
 * When `NEXT_PUBLIC_API_BASE_URL` is unset, the resolved base differs on server vs browser
 * (origin is only known in the client). Do not render this string during SSR unless you
 * gate on `useEffect` / `typeof window` after hydration (see `StatusPanel`).
 */
export function getPublicApiBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
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
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (explicit) return explicit.replace(/\/$/, "");
  if (typeof window !== "undefined") {
    return "same-origin /api/backend (set BACKEND_URL in Next .env.local; defaults to http://127.0.0.1:8000)";
  }
  return "same-origin /api/backend → " + (process.env.BACKEND_URL ?? "http://127.0.0.1:8000");
}
