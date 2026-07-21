# --- build stage ---
FROM rust:1.79-slim AS build
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release

# --- runtime stage (minimal, non-root, pin a real digest in production) ---
FROM debian:bookworm-slim AS runtime
RUN useradd --uid 1001 --create-home appuser \
    && apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app/target/release/production-grade-app ./app
USER appuser
EXPOSE 8080
CMD ["./app"]
