# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:22-slim AS build-stage

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN npm install -g pnpm && pnpm config set store-dir /app/node_modules/.pnpm-store

RUN pnpm install --frozen-lockfile

COPY . .

CMD ["pnpm", "run", "docker-dev"]
