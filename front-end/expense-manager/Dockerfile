# --- STAGE 1: BUILD ---
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copy dependency files first for better caching
COPY package*.json ./
RUN npm install

# Copy source and build the static files
COPY . .
RUN npm run build

# --- STAGE 2: PRODUCTION ---
FROM nginx:stable-alpine

# Remove the default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy YOUR custom nginx.conf from your project directory
# Adjust this path if your Docker context is already inside the expense-manager folder
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy the static 'dist' folder from the build-stage to Nginx's HTML folder
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Nginx serves on port 80 by default
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]