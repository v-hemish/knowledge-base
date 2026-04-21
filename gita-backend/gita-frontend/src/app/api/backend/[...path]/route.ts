import { NextRequest } from "next/server";

export const runtime = "nodejs";

const BACKEND = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

function buildTarget(pathSegments: string[], search: string): string {
  const joined = pathSegments.join("/");
  const base = `${BACKEND}/${joined}`;
  return search ? `${base}${search.startsWith("?") ? search : `?${search}`}` : base;
}

function forwardRequestHeaders(req: NextRequest): Headers {
  const h = new Headers();
  const ct = req.headers.get("content-type");
  if (ct) h.set("content-type", ct);
  const accept = req.headers.get("accept");
  if (accept) h.set("accept", accept);
  return h;
}

function forwardResponseHeaders(res: Response): Headers {
  const out = new Headers();
  const ct = res.headers.get("content-type");
  if (ct) out.set("content-type", ct);
  const cc = res.headers.get("cache-control");
  if (cc) out.set("cache-control", cc);
  const xc = res.headers.get("x-accel-buffering");
  if (xc) out.set("x-accel-buffering", xc);
  const te = res.headers.get("transfer-encoding");
  if (te) out.set("transfer-encoding", te);
  return out;
}

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const target = buildTarget(path, req.nextUrl.search);
  const res = await fetch(target, { method: "GET", cache: "no-store" });
  return new Response(res.body, {
    status: res.status,
    headers: forwardResponseHeaders(res),
  });
}

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const target = buildTarget(path, "");
  const buf = await req.arrayBuffer();
  const res = await fetch(target, {
    method: "POST",
    headers: forwardRequestHeaders(req),
    body: buf.byteLength ? buf : undefined,
    cache: "no-store",
  });
  return new Response(res.body, {
    status: res.status,
    headers: forwardResponseHeaders(res),
  });
}
