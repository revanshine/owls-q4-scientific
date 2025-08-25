# OWLS Archive Q4 - Fargate Container
# Self-contained scientific Q4 processing with modular structure

FROM python:3.12-slim

# Install uv for dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy the project configuration and lock file
COPY pyproject.toml .
COPY uv.lock .

# Copy the scientific Q4 modules
COPY q4/ ./q4/

# Copy the Fargate processing script
COPY fargate_processor.py .

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Set the entrypoint
ENTRYPOINT ["uv", "run", "python", "fargate_processor.py"]
