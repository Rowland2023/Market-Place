# Use a valid base image
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# COPY looks for files RELATIVE to the build context
# The context in docker-compose.yml should be: ./front-end/expense-manager
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the source code
COPY . .

# Expose the port (Vite default is 5173)
EXPOSE 5173

# FIX: Added --host to allow external access from your browser
CMD ["npm", "run", "dev", "--", "--host"]