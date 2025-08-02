# LoggiFly Helper

![LoggiFly Helper](icon.png)

A lightweight webhook receiver that logs LoggiFly notifications to files. Designed for Unraid and other Docker environments where you want to capture LoggiFly alerts in log files instead of external notification services.

## Features

- **Webhook Receiver**: Accepts POST requests from LoggiFly
- **Logs Everything**: All notifications from LoggiFly are logged (no filtering)
- **Flexible Logging**: Multiple log formats (detailed, simple, JSON)
- **Log Rotation**: Automatic log rotation with configurable size limits
- **Health Monitoring**: Built-in health check and stats endpoints
- **Unraid Optimized**: Fully configurable via environment variables
- **Non-Root**: Runs as non-privileged user for security

## Quick Start

### Docker Run
```bash
docker run -d \
  --name loggifly-helper \
  -p 5353:5353 \
  -v /path/to/logs:/logs \
  -e LOG_LEVEL=INFO \
  aidrak/loggifly-helper:latest
```

### Unraid Template
- **Repository**: `aidrak/loggifly-helper:latest`
- **Port**: `5353:5353`
- **Volume**: `/mnt/user/appdata/loggifly-helper/logs:/logs`
- **Environment**: `LOG_FORMAT=detailed` (optional)

## Environment Variables

### Core Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5353` | Port to listen on |
| `HOST` | `0.0.0.0` | Host interface to bind |
| `LOG_FILE` | `/logs/loggifly-notifications.log` | Path to log file |

### Log Formatting
| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_FORMAT` | `detailed` | Log format: `detailed`, `simple`, or `json` |
| `LOG_ROTATION` | `true` | Enable log rotation |
| `MAX_LOG_SIZE` | `10MB` | Maximum log file size before rotation |
| `BACKUP_COUNT` | `5` | Number of rotated log files to keep |

### Performance
| Variable | Default | Description |
|----------|---------|-------------|
| `WORKERS` | `1` | Number of Gunicorn workers (use >1 for high load) |

## Log Formats

### Detailed (Default)
```
2025-08-02T10:30:15.123456 - INFO - Container: nginx | Keyword: error | Message: 404 Not Found
```

### Simple
```
2025-08-02T10:30:15.123456 - nginx | error | 404 Not Found
```

### JSON
```json
{"timestamp": "2025-08-02T10:30:15.123456", "level": "INFO", "message": {"timestamp": "2025-08-02T10:30:15.123456", "container": "nginx", "keyword": "error", "message": "404 Not Found", "raw_data": {...}}}
```

## LoggiFly Configuration

Configure LoggiFly to send webhooks to this container:

### Environment Variables
```bash
WEBHOOK_URL=http://your-server-ip:5353/webhook
```

### Config.yaml
```yaml
notifications:
  webhook:
    url: http://your-server-ip:5353/webhook
    headers:
      Content-Type: "application/json"

containers:
  your-container:
    keywords:
      - error
      - failed
```

## API Endpoints

- **POST** `/webhook` - Receive LoggiFly notifications
- **GET** `/health` - Health check endpoint
- **GET** `/config` - Show current configuration
- **GET** `/stats` - Show log file statistics

## Testing

Test the webhook endpoint:
```bash
curl -X POST http://your-server:5353/webhook \
  -H "Content-Type: application/json" \
  -d '{"container":"test","keyword":"test","message":"Test notification"}'
```

Check health:
```bash
curl http://your-server:5353/health
```

## Building

```bash
docker build -t loggifly-helper .
```

## License

MIT License