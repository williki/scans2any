FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set up working directory
WORKDIR /app

# Copy the application code
COPY pyproject.toml uv.lock README.md src /app

# Create a virtual environment and install dependencies
RUN uv sync --no-cache-dir

# Set the entrypoint
ENTRYPOINT ["uv", "run", "--no-cache-dir", "scans2any"]
CMD ["--help"]
