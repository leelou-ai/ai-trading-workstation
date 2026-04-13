# Stage 1: Build Next.js frontend
FROM node:20-slim AS frontend-builder
WORKDIR /build/frontend

# Copy frontend and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source and build
COPY frontend/ ./
RUN npm run build
# Output is in /build/frontend/out/

# Stage 2: Python backend + serve everything
FROM python:3.12-slim AS final

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy backend dependency files and sync (production only)
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --no-dev --frozen

# Copy backend source
COPY backend/app/ ./app/

# Copy frontend build output to /app/static/
COPY --from=frontend-builder /build/frontend/out/ ./static/

# Create db directory (will be volume-mounted at runtime)
RUN mkdir -p /app/db

# Expose port
EXPOSE 8000

# Environment defaults
ENV DB_PATH=/app/db/finally.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run with uvicorn via uv (ensures virtual environment is activated)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
