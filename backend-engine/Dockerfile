FROM python:3.12-slim-bookworm

WORKDIR /app

# Install curl for healthcheck and uv via official installer
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files AND source BEFORE uv sync (required for editable install)
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Install dependencies AND project (--frozen uses lockfile exactly, --no-dev skips dev deps)
RUN uv sync --frozen --no-dev

# Create data directory for local storage
RUN mkdir -p /data

EXPOSE 8000

# Run with uv run to ensure command runs in the uv environment
CMD ["uv", "run", "uvicorn", "vulnerable_banana.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
