# ── Frontend — AgroCycle Next.js web app ─────────────────────────────────────
# Multi-stage build using Next.js standalone output (output: "standalone" in
# next.config.ts) so the final image contains only the files the server needs.

# ── Stage 1: install dependencies ─────────────────────────────────────────────
FROM node:20-alpine AS deps

RUN corepack enable && corepack prepare pnpm@10 --activate

WORKDIR /app

# Copy lockfiles first so this layer is cached when only source changes.
COPY package.json pnpm-lock.yaml ./
# postinstall runs scripts/copy-maplibre-worker.mjs, so the scripts dir must exist.
COPY scripts/ ./scripts/
RUN pnpm install --frozen-lockfile


# ── Stage 2: build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

RUN corepack enable && corepack prepare pnpm@10 --activate

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# AGROCYCLE_API_URL is a server-side env var — set it at runtime, not build
# time, so the same image works in any environment.
# NEXT_TELEMETRY_DISABLED silences the Next.js telemetry prompt.
ENV NEXT_TELEMETRY_DISABLED=1

RUN pnpm run build


# ── Stage 3: runtime image ────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

RUN addgroup --system --gid 1001 nodejs && \
    adduser  --system --uid 1001 nextjs

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3004
ENV HOSTNAME=0.0.0.0

# Copy only the standalone server and static assets produced by next build.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static     ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public           ./public

USER nextjs
EXPOSE 3004

CMD ["node", "server.js"]
