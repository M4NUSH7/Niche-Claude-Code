# --- build stage ---
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

# --- runtime stage (non-root, standalone Next output recommended) ---
FROM node:20-slim AS runtime
RUN useradd --uid 1001 --create-home appuser
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/public ./public
USER appuser
EXPOSE 3000
CMD ["npm", "start"]
