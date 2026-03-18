FROM python:3.11-slim AS builder

WORKDIR /app


COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app


COPY --from=builder /install /usr/local
COPY . .

RUN addgroup --system hrce && adduser --system --ingroup hrce hrce
USER hrce

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
