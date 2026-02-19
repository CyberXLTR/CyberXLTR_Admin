# CyberXLTR Admin Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use npm install since package-lock.json may not exist)
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3001

# Default command (overridden by docker-compose for dev)
CMD ["npm", "run", "dev"]

