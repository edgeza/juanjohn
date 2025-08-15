FROM node:20-alpine

# Fix for some native modules and ensure compatibility
RUN apk add --no-cache libc6-compat

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./

# Public runtime values must be present at build time for Next.js to inline them
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}

RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build the Next.js app for production
RUN npm run build

ENV NODE_ENV=production
ENV PORT=3001

# Prepare standalone runtime directory with static assets and public files
RUN mkdir -p .next/standalone/.next \
    && cp -r .next/static .next/standalone/.next/static \
    && mkdir -p .next/standalone/public \
    && if [ -d public ]; then cp -r public/* .next/standalone/public/ || true; fi

# Create and use non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 \
    && chown -R nextjs:nodejs /app

WORKDIR /app/.next/standalone
USER nextjs

# Expose port
EXPOSE 3001

# Start the application (standalone server)
CMD ["node", "server.js"]
