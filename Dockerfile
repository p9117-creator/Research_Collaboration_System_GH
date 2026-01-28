# Research Collaboration System - API Service Dockerfile (Multi-stage)

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a prefix location
COPY requirements.txt .
RUN mkdir -p /install
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libfreetype6 \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder stage to global location
COPY --from=builder /install /usr/local

# Copy application code
COPY code/ /app/code/
COPY docs/ /app/docs/

# Create non-root user (good security practice)
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "code/api_server.py"]
