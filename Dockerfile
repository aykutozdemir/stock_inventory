# Multi-stage Dockerfile for Electronic Component Inventory

# Stage 1: Builder stage for Python dependencies
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Note: llama-cpp-python may need to be installed separately if CUDA is needed
# For CPU-only: pip install llama-cpp-python
# For CUDA: pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu123

# Stage 2: Runtime stage
FROM python:3.12-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user for security
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app \
    && chown -R app:app /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=app:app backend/ ./backend/
COPY --chown=app:app frontend/ ./frontend/
COPY --chown=app:app app.py ./
COPY --chown=app:app tray_app.py ./
COPY --chown=app:app hardware_detector.py ./
COPY --chown=app:app print_selected_model.py ./

# Copy model files into the image (models are required for the application)
COPY --chown=app:app models/ ./models/

# Create necessary directories
RUN mkdir -p uploads memory logs data \
    && chown -R app:app uploads models memory logs data

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production \
    FLASK_DEBUG=false \
    PYTHONPATH=/app \
    DATABASE=/app/data/inventory.db \
    UPLOAD_FOLDER=/app/uploads \
    MODEL_DIR=/app/models \
    MEMORY_DIR=/app/memory \
    LOG_FILE=/app/logs/app.log

# Start application
CMD ["python", "backend/app.py"]
