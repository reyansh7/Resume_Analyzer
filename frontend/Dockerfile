FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
# Install all dependencies for build
RUN npm ci

COPY . .

# Set NODE_ENV to production for optimized build
ENV NODE_ENV=production
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install Next.js runtime
RUN npm install -g next

# Copy only necessary files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./
COPY --from=builder /app/package-lock.json ./
COPY --from=builder /app/next.config.mjs ./

# Install only production dependencies
RUN npm ci --only=production

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

EXPOSE 3000

# Run as non-root user for security
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs

ENV NODE_ENV=production
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL:-http://localhost:8080/api}

CMD ["npm", "run", "start"]
