# StreamVault Pro - Professional Live Stream Recording Platform
# Multi-stage build for optimized image size

FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLATFORM=web \
    HOST=0.0.0.0 \
    PORT=8080

# Install system dependencies and FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create application directory and user
RUN useradd --create-home --shell /bin/bash streamvault
WORKDIR /home/streamvault/app
USER streamvault

# Copy application code
COPY --chown=streamvault:streamvault . .

# Create necessary directories
RUN mkdir -p downloads config logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

# Expose port
EXPOSE 8080

# Set volume for persistent data
VOLUME ["/home/streamvault/app/downloads", "/home/streamvault/app/config", "/home/streamvault/app/logs"]

# Start command
CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "8080"]