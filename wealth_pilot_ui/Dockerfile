FROM node:20-alpine
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# In dev mode, source code is mounted as a volume
# No need to COPY application code — it's bind-mounted

EXPOSE 3000

# Use next dev for hot reload during development
CMD ["npm", "run", "dev"]
