FROM node:18-alpine AS deps

RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:18-alpine AS builder

RUN apk update && apk add --no-cache git
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Export estático: sin servidor Node, todo el chat/RAG/modelo corre en el
# navegador de cada usuario. BUILD_MODE=export ya es el default de
# next.config.mjs, se deja explícito acá para que quede claro.
ENV BUILD_MODE=export
RUN npm run export

FROM nginx:1.27-alpine AS runner

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/out /usr/share/nginx/html

EXPOSE 80
