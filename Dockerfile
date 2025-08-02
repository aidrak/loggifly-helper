FROM python:3.11-slim

LABEL maintainer="Your Name"
LABEL description="LoggiFly Helper - Webhook receiver for logging LoggiFly notifications"
LABEL version="1.0"

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask gunicorn

# Create non-root user
RUN useradd -m -u 999 loggifly && \
    mkdir -p /logs && \
    chown -R loggifly:loggifly /logs /app

# Copy application files
COPY app.py /app/
COPY entrypoint.sh /app/
COPY icon.png /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh && \
    chown loggifly:loggifly /app/app.py /app/entrypoint.sh /app/icon.png

# Switch to non-root user
USER loggifly

# Expose port
EXPOSE 5353

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5353}/health || exit 1

# Set default environment variables
ENV PORT=5353 \
    HOST=0.0.0.0 \
    LOG_FILE=/logs/loggifly-notifications.log \
    LOG_FORMAT=detailed \
    LOG_ROTATION=true \
    MAX_LOG_SIZE=10MB \
    BACKUP_COUNT=5 \
    WORKERS=1

ENTRYPOINT ["/app/entrypoint.sh"]