# ── Stage 1: build deps ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source
COPY src/ ./src/
COPY skills/ ./skills/
COPY pyproject.toml .

# Default transport is HTTP when running in a container
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9002

EXPOSE 9002

CMD ["python", "-m", "src.server"]
