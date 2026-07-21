# --- build stage ---
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir --target=/deps .
COPY . .

# --- runtime stage (minimal, non-root, pin a real digest in production) ---
FROM python:3.12-slim AS runtime
RUN useradd --uid 1001 --create-home appuser
WORKDIR /app
COPY --from=build /deps /usr/local/lib/python3.12/site-packages
COPY --from=build /app /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
