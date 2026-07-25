FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_PROFILE=observer \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_ALLOWED_CWDS=/workspace

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin mcp-agent \
    && mkdir -p /workspace \
    && chown -R mcp-agent:mcp-agent /app /workspace

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"

CMD ["mcp-server-gateway"]
