import { Hono } from "hono";
import { cors } from "hono/cors";

type Bindings = { DB: D1Database; ASSETS: R2Bucket; CACHE: KVNamespace };
const app = new Hono<{ Bindings: Bindings }>();

// Static CORS allowlist — never reflect Origin when credentials are involved. See references/security.md.
app.use(
  "*",
  cors({
    origin: (origin) => (ALLOWED_ORIGINS.includes(origin ?? "") ? origin : undefined),
    credentials: true,
  })
);
const ALLOWED_ORIGINS: string[] = [];

app.get("/healthz", (c) => c.json({ status: "ok" }));

// Mount versioned routes: app.route("/v1", v1Router)
// No persistent process — initialize D1/R2/KV clients per-request via c.env, not module-level state.

export default app;
