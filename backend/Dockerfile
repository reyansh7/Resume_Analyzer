FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
# Install all dependencies (including dev) for build
RUN npm ci

# Copy application code
COPY src ./src
COPY tsconfig.json ./tsconfig.json

# Build TypeScript
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy production dependencies
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Copy built application from builder
COPY --from=builder /app/dist ./dist

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

EXPOSE 8080

# Run as non-root user for security
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs

CMD ["npm", "run", "start"]
