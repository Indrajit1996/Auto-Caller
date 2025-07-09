# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:22-slim AS build-stage

WORKDIR /app

COPY package.json package-lock.json ./

# Clean install to avoid architecture issues
RUN rm -rf node_modules package-lock.json && \
    npm install

COPY . .

CMD ["npm", "run", "docker-dev"]
