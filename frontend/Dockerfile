# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:22-slim AS build-stage

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN npm install -g pnpm

RUN pnpm install

ENV ROLLUP_USE_NODE_JS=true

COPY . .

CMD ["pnpm", "run", "docker-dev"]
