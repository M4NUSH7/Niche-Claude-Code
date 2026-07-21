import express from "express";
import helmet from "helmet";
import cors from "cors";

// See references/security.md: static CORS allowlist, never reflect Origin when credentials:true.
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS ?? "").split(",").filter(Boolean);

const app = express();

app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        // Replace with per-request nonce in production — see references/security.md.
        scriptSrc: ["'self'"],
        frameAncestors: ["'none'"],
      },
    },
  })
);

app.use(
  cors({
    origin: (origin, callback) => {
      if (!origin || ALLOWED_ORIGINS.includes(origin)) return callback(null, true);
      return callback(new Error("Origin not allowed"));
    },
    credentials: true,
  })
);

app.use(express.json());

// Mount versioned API routes here: app.use("/v1", v1Router)
app.get("/healthz", (_req, res) => res.status(200).json({ status: "ok" }));

const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => {
  // Replace with structured (pino) logging — see references/infrastructure-delivery.md.
  console.log(`listening on :${port}`);
});
