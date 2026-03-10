FROM python:3.12-slim

# Build arguments for iFlow installation
ARG IFLOW_INSTALL_CMD="npm install -g iflow"
ARG IFLOW_NPM_PACKAGE="iflow"
ARG WEBHOOK_PORT=8080

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV WEBHOOK_PORT=${WEBHOOK_PORT}

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for iFlow CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && npm --version

# Install iFlow CLI
# Use build arg to customize installation: --build-arg IFLOW_NPM_PACKAGE=your-iflow-package
ARG IFLOW_NPM_PACKAGE=@iflow-ai/iflow-cli
RUN npm install -g ${IFLOW_NPM_PACKAGE} && \
    which iflow && iflow --version || echo "iFlow installation attempted"

# Copy application code first for editable install
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p /app/repos /app/.issue-automator

# Expose webhook port
EXPOSE ${WEBHOOK_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${WEBHOOK_PORT}/health || exit 1

# Default command
CMD ["sh", "-c", "issue-automator automation start --host 0.0.0.0 --port ${WEBHOOK_PORT} --work-dir /app/repos"]
