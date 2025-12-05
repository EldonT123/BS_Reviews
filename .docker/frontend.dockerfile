# .docker/frontend.dockerfile

# Use official Node image
FROM node:20-slim

# Set working directory inside container
WORKDIR /app

# Copy package files first (for caching)
COPY frontend/bs_reviews/package.json frontend/bs_reviews/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy the rest of the frontend source code
COPY frontend/bs_reviews/ ./

# Expose Next.js dev port
EXPOSE 3000

# Start Next.js in dev mode
CMD ["npm", "run", "dev"]