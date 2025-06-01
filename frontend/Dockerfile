# Use Node.js 18 Alpine image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with legacy peer deps to handle React 19 compatibility
RUN npm ci --legacy-peer-deps

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 