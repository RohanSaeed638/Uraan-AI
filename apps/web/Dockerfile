# The web image. Build from the repository root (it is an npm workspace):
#   docker build -f apps/web/Dockerfile -t uraan-web \
#     --build-arg NEXT_PUBLIC_API_URL=https://api.example.com \
#     --build-arg NEXT_PUBLIC_SUPABASE_URL=... --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=... .
# NEXT_PUBLIC_* values are baked in at build time, so they are build arguments.
FROM node:22-slim AS deps
WORKDIR /repo
COPY package.json package-lock.json .npmrc ./
COPY apps/web/package.json apps/web/package.json
COPY packages packages
RUN npm ci --workspace apps/web --include-workspace-root

FROM node:22-slim AS build
WORKDIR /repo
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    NEXT_PUBLIC_SENTRY_DSN=$NEXT_PUBLIC_SENTRY_DSN \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_OUTPUT=standalone \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /repo/node_modules node_modules
COPY . .
RUN npm run build --workspace apps/web

FROM node:22-slim AS run
WORKDIR /repo
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build /repo/apps/web/.next/standalone ./
COPY --from=build /repo/apps/web/.next/static apps/web/.next/static
COPY --from=build /repo/apps/web/public apps/web/public
USER node
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
