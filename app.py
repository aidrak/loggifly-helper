#!/usr/bin/env python3
import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request

app = Flask(__name__)

# Environment variable configuration
PORT = int(os.getenv('PORT', 5353))
HOST = os.getenv('HOST', '0.0.0.0')
LOG_FILE = os.getenv('LOG_FILE', '/logs/loggifly-notifications.log')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'detailed')  # detailed, simple, json
LOG_ROTATION = os.getenv('LOG_ROTATION', 'true').lower() == 'true'
MAX_LOG_SIZE = os.getenv('MAX_LOG_SIZE', '10MB')
BACKUP_COUNT = int(os.getenv('BACKUP_COUNT', 5))

def setup_logging():
    """Configure logging to capture all notifications"""
    
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure log format based on LOG_FORMAT env var
    if LOG_FORMAT == 'json':
        log_format = '{"timestamp": "%(asctime)s", "message": %(message)s}'
    elif LOG_FORMAT == 'simple':
        log_format = '%(asctime)s - %(message)s'
    else:  # detailed
        log_format = '%(asctime)s - %(message)s'
    
    # Convert size string to bytes
    def parse_size(size_str):
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    # Setup handlers
    handlers = []
    
    if LOG_ROTATION:
        max_bytes = parse_size(MAX_LOG_SIZE)
        file_handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=max_bytes, 
            backupCount=BACKUP_COUNT
        )
    else:
        file_handler = logging.FileHandler(LOG_FILE)
    
    file_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(file_handler)
    
    # Console handler for container logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    handlers.append(console_handler)
    
    # Configure root logger - always log everything
    logging.basicConfig(
        level=logging.INFO,  # Fixed at INFO level
        handlers=handlers,
        force=True
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle LoggiFly webhook notifications - logs everything received"""
    try:
        # Get request data
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = request.get_json() or {}
        else:
            # Handle plain text or other formats
            raw_data = request.data.decode('utf-8')
            data = {'message': raw_data}
        
        # Extract LoggiFly data with defaults
        container = data.get('container', 'unknown')
        keyword = data.get('keyword', data.get('keywords', 'unknown'))
        message = data.get('message', data.get('title', data.get('body', 'No message')))
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Format log entry based on LOG_FORMAT
        if LOG_FORMAT == 'json':
            log_entry = json.dumps({
                'timestamp': timestamp,
                'container': container,
                'keyword': keyword,
                'message': message,
                'raw_data': data
            })
        elif LOG_FORMAT == 'simple':
            log_entry = f"{container} | {keyword} | {message}"
        else:  # detailed
            log_entry = f"Container: {container} | Keyword: {keyword} | Message: {message}"
        
        # Always log every notification received
        logger.info(log_entry)
        
        return {'status': 'success', 'message': 'Notification logged'}, 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Basic health check - verify log file is writable
        with open(LOG_FILE, 'a'):
            pass
        return {
            'status': 'healthy',
            'log_file': LOG_FILE,
            'version': '1.0'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 500

@app.route('/config', methods=['GET'])
def config():
    """Show current configuration"""
    return {
        'port': PORT,
        'host': HOST,
        'log_file': LOG_FILE,
        'log_format': LOG_FORMAT,
        'log_rotation': LOG_ROTATION,
        'max_log_size': MAX_LOG_SIZE,
        'backup_count': BACKUP_COUNT
    }, 200

@app.route('/stats', methods=['GET'])
def stats():
    """Show log file statistics"""
    try:
        import glob
        
        # Get main log file size
        main_size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
        
        # Get rotated log files
        log_pattern = f"{LOG_FILE}.*"
        rotated_files = glob.glob(log_pattern)
        
        return {
            'log_file': LOG_FILE,
            'main_log_size': main_size,
            'rotated_files': len(rotated_files),
            'total_files': len(rotated_files) + (1 if main_size > 0 else 0)
        }, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/icon.png', methods=['GET'])
def icon():
    """Serve the container icon for Unraid"""
    try:
        from flask import send_file
        return send_file('/app/icon.png', mimetype='image/png')
    except Exception as e:
        return {'error': str(e)}, 404

if __name__ == '__main__':
    logger.info(f"Starting LoggiFly Helper on {HOST}:{PORT}")
    logger.info(f"Log configuration: file={LOG_FILE}, format={LOG_FORMAT}")
    logger.info(f"Log rotation: enabled={LOG_ROTATION}, max_size={MAX_LOG_SIZE}, backups={BACKUP_COUNT}")
    logger.info("Ready to log ALL notifications from LoggiFly")
    
    app.run(host=HOST, port=PORT, debug=False)#!/usr/bin/env python3
import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request

app = Flask(__name__)

# Environment variable configuration
PORT = int(os.getenv('PORT', 5353))
HOST = os.getenv('HOST', '0.0.0.0')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', '/logs/loggifly-notifications.log')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'detailed')  # detailed, simple, json
LOG_ROTATION = os.getenv('LOG_ROTATION', 'true').lower() == 'true'
MAX_LOG_SIZE = os.getenv('MAX_LOG_SIZE', '10MB')
BACKUP_COUNT = int(os.getenv('BACKUP_COUNT', 5))

def setup_logging():
    """Configure logging based on environment variables"""
    
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure log format based on LOG_FORMAT env var
    if LOG_FORMAT == 'json':
        log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
    elif LOG_FORMAT == 'simple':
        log_format = '%(asctime)s - %(message)s'
    else:  # detailed
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Convert size string to bytes
    def parse_size(size_str):
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    # Setup handlers
    handlers = []
    
    if LOG_ROTATION:
        max_bytes = parse_size(MAX_LOG_SIZE)
        file_handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=max_bytes, 
            backupCount=BACKUP_COUNT
        )
    else:
        file_handler = logging.FileHandler(LOG_FILE)
    
    file_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(file_handler)
    
    # Console handler for container logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=handlers,
        force=True
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle LoggiFly webhook notifications"""
    try:
        # Get request data
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = request.get_json() or {}
        else:
            # Handle plain text or other formats
            raw_data = request.data.decode('utf-8')
            data = {'message': raw_data}
        
        # Extract LoggiFly data with defaults
        container = data.get('container', 'unknown')
        keyword = data.get('keyword', data.get('keywords', 'unknown'))
        message = data.get('message', data.get('title', data.get('body', 'No message')))
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Format log entry based on LOG_FORMAT
        if LOG_FORMAT == 'json':
            log_entry = json.dumps({
                'timestamp': timestamp,
                'container': container,
                'keyword': keyword,
                'message': message,
                'raw_data': data
            })
        elif LOG_FORMAT == 'simple':
            log_entry = f"{container} | {keyword} | {message}"
        else:  # detailed
            log_entry = f"Container: {container} | Keyword: {keyword} | Message: {message}"
        
        # Log the notification
        logger.info(log_entry)
        
        # Debug log full payload if debug level
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Full webhook payload: {json.dumps(data, indent=2)}")
        
        return {'status': 'success', 'message': 'Notification logged'}, 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Basic health check - verify log file is writable
        with open(LOG_FILE, 'a'):
            pass
        return {
            'status': 'healthy',
            'log_file': LOG_FILE,
            'log_level': LOG_LEVEL,
            'version': '1.0'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 500

@app.route('/config', methods=['GET'])
def config():
    """Show current configuration"""
    return {
        'port': PORT,
        'host': HOST,
        'log_level': LOG_LEVEL,
        'log_file': LOG_FILE,
        'log_format': LOG_FORMAT,
        'log_rotation': LOG_ROTATION,
        'max_log_size': MAX_LOG_SIZE,
        'backup_count': BACKUP_COUNT
    }, 200

@app.route('/stats', methods=['GET'])
def stats():
    """Show log file statistics"""
    try:
        import glob
        
        # Get main log file size
        main_size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
        
        # Get rotated log files
        log_pattern = f"{LOG_FILE}.*"
        rotated_files = glob.glob(log_pattern)
        
        return {
            'log_file': LOG_FILE,
            'main_log_size': main_size,
            'rotated_files': len(rotated_files),
            'total_files': len(rotated_files) + (1 if main_size > 0 else 0)
        }, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/icon.png', methods=['GET'])
def icon():
    """Serve the container icon for Unraid"""
    try:
        from flask import send_file
        return send_file('/app/icon.png', mimetype='image/png')
    except Exception as e:
        return {'error': str(e)}, 404

if __name__ == '__main__':
    logger.info(f"Starting LoggiFly Helper on {HOST}:{PORT}")
    logger.info(f"Log configuration: file={LOG_FILE}, level={LOG_LEVEL}, format={LOG_FORMAT}")
    logger.info(f"Log rotation: enabled={LOG_ROTATION}, max_size={MAX_LOG_SIZE}, backups={BACKUP_COUNT}")
    
    app.run(host=HOST, port=PORT, debug=(LOG_LEVEL == 'DEBUG'))