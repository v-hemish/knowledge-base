/** GET /health */
export interface HealthLiveness {
  status: string;
}

/** GET /health/ready — shape may evolve; keep loose + narrow in UI */
export interface HealthReadyResponse {
  status: "ready" | "degraded" | string;
  components?: Record<
    string,
    {
      ok: boolean;
      detail?: string | null;
      path?: string;
      url?: string;
    }
  >;
}

/** GET /api/v1/version */
export interface ApiVersionResponse {
  api: string;
  package_version: string;
}
