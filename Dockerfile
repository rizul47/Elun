# ============================================
# Stage 1: Build the React Frontend
# ============================================
FROM node:18-slim AS frontend-build

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source
COPY . .

# Build the React app (outputs to backend/dist)
RUN npm run build

# ============================================
# Stage 2: Set up the Python Backend
# ============================================
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV, PyTorch, and fonts
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend folder
COPY backend/ ./backend/

# Copy the built frontend from Stage 1
COPY --from=frontend-build /app/backend/dist ./backend/dist

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p backend/test_img \
    && mkdir -p backend/Real-ESRGAN/inputs \
    && mkdir -p backend/Real-ESRGAN/results \
    && mkdir -p "backend/Divided Regions"

# Set working directory to backend
WORKDIR /app/backend

# Hugging Face Spaces uses port 7860
EXPOSE 7860

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
