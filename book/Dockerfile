FROM node:20-alpine

WORKDIR /app

# Copy dependency files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose the server port
EXPOSE 3000

# Run Docusaurus with host binding to allow external connections
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0"]
