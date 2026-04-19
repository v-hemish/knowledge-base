"use client";

import { useEffect, useState } from "react";
import { apiJson } from "@/lib/api/client";
import type { ApiVersionResponse, HealthLiveness, HealthReadyResponse } from "@/types/api";
import { getConfiguredApiLabel, getPublicApiBaseUrl } from "@/lib/api/config";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function StatusPanel() {
  const [health, setHealth] = useState<HealthLiveness | null>(null);
  const [ready, setReady] = useState<HealthReadyResponse | null>(null);
  const [version, setVersion] = useState<ApiVersionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  /** Resolved after mount so SSR HTML matches first client paint (avoids window vs server mismatch). */
  const [apiBaseDisplay, setApiBaseDisplay] = useState("—");
  const [apiLabelDisplay, setApiLabelDisplay] = useState("—");

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [h, r, v] = await Promise.all([
        apiJson<HealthLiveness>("/health"),
        apiJson<HealthReadyResponse>("/health/ready"),
        apiJson<ApiVersionResponse>("/api/v1/version"),
      ]);
      setHealth(h);
      setReady(r);
      setVersion(v);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setApiBaseDisplay(getPublicApiBaseUrl());
    setApiLabelDisplay(getConfiguredApiLabel());
  }, []);

  useEffect(() => {
    void load();
    const id = setInterval(() => void load(), 15_000);
    return () => clearInterval(id);
  }, []);

  const readyLabel = ready?.status ?? "—";

  return (
    <Card className="border-dashed border-stone-300/90 bg-stone-50/50">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-stone-700">Backend status</CardTitle>
        <Button type="button" variant="ghost" size="sm" onClick={() => void load()} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        </Button>
      </CardHeader>
      <CardContent className="space-y-2 text-xs text-stone-600">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-stone-500">Base URL</span>
          <code className="rounded bg-white px-1.5 py-0.5 text-[11px] text-stone-800">
            {apiBaseDisplay}
          </code>
        </div>
        <p className="text-[11px] text-stone-500">Configured: {apiLabelDisplay}</p>
        {err ? <p className="text-amber-800">{err}</p> : null}
        <div className="grid gap-1 sm:grid-cols-3">
          <div>
            <p className="text-stone-500">/health</p>
            <Badge variant="muted">{health?.status ?? "—"}</Badge>
          </div>
          <div>
            <p className="text-stone-500">/health/ready</p>
            <Badge variant="muted">{readyLabel}</Badge>
          </div>
          <div>
            <p className="text-stone-500">/api/v1/version</p>
            <Badge variant="muted">{version?.package_version ?? "—"}</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
