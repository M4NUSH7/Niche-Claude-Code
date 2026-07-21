from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# See references/security.md: static CORS allowlist, never reflect Origin when credentials=True.
ALLOWED_ORIGINS = [o for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o]

app = FastAPI(title="production-grade-app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    # Replace script-src with a per-request nonce in production - see references/security.md.
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# Mount versioned routers here: app.include_router(v1_router, prefix="/v1")
