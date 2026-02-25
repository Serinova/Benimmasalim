# Development stage (optional, for local dev only)
FROM node:20-alpine AS development

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build - backend URL for server proxy + client direct API calls
ARG BACKEND_INTERNAL_URL=http://127.0.0.1:8000
ARG NEXT_PUBLIC_API_URL=
ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}
# Client-side fetch uses this; set to backend API base so browser calls backend directly (no proxy)
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Production stage (MUST be last — Docker uses last stage as default)
FROM node:20-alpine AS runner

WORKDIR /app

# Proxy backend URL — must be set at runtime (build-arg baked in; Cloud Run can override)
ARG BACKEND_INTERNAL_URL=http://127.0.0.1:8000
ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Install sharp for Next.js image optimization (standalone mode)
RUN npm i --no-save sharp

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
