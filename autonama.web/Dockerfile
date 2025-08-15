FROM node:20-alpine

# Fix for some native modules and ensure compatibility
RUN apk add --no-cache libc6-compat

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build the Next.js app for production
RUN npm run build

# Use a non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 \
    && chown -R nextjs:nodejs /app
USER nextjs

ENV NODE_ENV=production

# Expose port
EXPOSE 3001

# Start the application (production server)
CMD ["npm", "run", "start", "--", "-p", "3001"]
