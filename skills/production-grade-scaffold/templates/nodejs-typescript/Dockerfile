# --- build stage ---
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

# --- runtime stage (minimal, non-root, pinned digest recommended in real use) ---
FROM node:20-slim AS runtime
RUN useradd --uid 1001 --create-home appuser
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
USER appuser
EXPOSE 3000
CMD ["node", "dist/api/server.js"]
