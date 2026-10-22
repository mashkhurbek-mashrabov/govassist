# syntax=docker/dockerfile:1

# ── build: typecheck + Vite build ─────────────────────────────────────────────
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --ignore-scripts --no-audit --no-fund
COPY . .
RUN npm run build && rm -f dist/mockServiceWorker.js

# ── runtime: static files + reverse proxy, non-root on 8080 ───────────────────
FROM nginxinc/nginx-unprivileged:1.31-alpine-slim AS runtime
ENV BACKEND_HOST=backend:8000 \
    ADMIN_URL=admin/ \
    NGINX_ENVSUBST_FILTER="^(BACKEND_HOST|ADMIN_URL)$"
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
