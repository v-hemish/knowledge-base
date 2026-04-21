# Gita guidance — Next.js frontend (MVP)

Polished **single-page** UI to exercise the retrieval-first backend: verse cards first, optional streamed explanation, no auth and no client database.

To run **API + UI together** from the parent folder, use **`make dev`** (see `../README.md`).

## Quick start

```bash
cd gita-frontend
cp .env.local.example .env.local
# edit .env.local — see "Backend connection" below
pnpm install   # or: npm install
pnpm dev       # or: npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Backend connection

**Option A — direct (needs CORS on FastAPI)**

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Add to your FastAPI app, for example:

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Option B — same-origin proxy (no CORS on FastAPI)**

Leave `NEXT_PUBLIC_API_BASE_URL` empty or unset. The app will call `/api/backend/...` on the Next server, which forwards to:

```env
BACKEND_URL=http://127.0.0.1:8000
```

(`BACKEND_URL` is **server-only**; put it in `.env.local`.)

## File tree

```text
src/
  app/
    layout.tsx, page.tsx, globals.css
    api/backend/[...path]/route.ts   # optional reverse proxy
  components/
    guidance/   # GuidanceApp, ChatComposer, VerseCard, VerseList, ExplanationStream, …
    status/       # StatusPanel
    ui/           # shadcn-style primitives (button, card, …)
  hooks/
    useGuidanceStream.ts
  lib/
    api/          # config, client, guidance, adapters
    sse/          # incremental SSE parsing
    utils.ts      # cn()
  types/
    guidance.ts, api.ts
```

## Types & adapters

- **`src/types/guidance.ts`** — Retrieve and stream DTOs aligned with FastAPI.
- **`src/lib/api/adapters.ts`** — **Single place** to adjust if field names or SSE JSON shape changes.

## SSE parsing

- **`src/lib/sse/guidanceStream.ts`** — Reads `ReadableStream`, splits on blank line (`\n\n`), keeps only `data:` lines, caps line length before `JSON.parse`, yields typed envelopes or parse warnings.
- **`src/hooks/useGuidanceStream.ts`** — Wires the parser to React state, supports **AbortController** cancel.

If the backend changes event names or payload shapes, update **`adapters.ts`** and optionally **`guidanceStream.ts`** (frame delimiter is still standard SSE).

## Scripts

| Command   | Purpose        |
|-----------|----------------|
| `pnpm dev` | Dev server     |
| `pnpm build` / `pnpm start` | Production |
| `pnpm lint` | ESLint        |

## Principles (UI)

- Structured **guidance result**, not a chat transcript.
- **Verse cards** are primary; streamed text is secondary.
- All verse **copy** is shown as returned by the API.
