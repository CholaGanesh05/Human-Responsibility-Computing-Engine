# ─── Stage 1: Build dependencies ──────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app


COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Runtime image ───────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app


# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system hrce && adduser --system --ingroup hrce hrce

# Set PYTHONPATH so 'app' package is importable
ENV PYTHONPATH=/app

USER hrce

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Use --reload only in dev (overridden by docker-compose command for worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
