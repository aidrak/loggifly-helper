#!/usr/bin/env python3
import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, request, send_file

app = Flask(__name__)

# Environment variable configuration
PORT = int(os.getenv('PORT', 5353))
HOST = os.getenv('HOST', '0.0.0.0')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
NOTIFICATIONS_LOG = os.getenv('NOTIFICATIONS_LOG', '/data/logs/loggifly.log')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'detailed')  # detailed, simple, json
LOG_ROTATION = os.getenv('LOG_ROTATION', 'true').lower() == 'true'
MAX_LOG_SIZE = os.getenv('MAX_LOG_SIZE', '10MB')
BACKUP_COUNT = int(os.getenv('BACKUP_COUNT', 5))

def setup_logging():
    """Configure logging - notifications to file, internal to console only"""
    
    # Ensure notifications log directory exists
    notifications_dir = os.path.dirname(NOTIFICATIONS_LOG)
    if notifications_dir:
        os.makedirs(notifications_dir, exist_ok=True)
    
    # Convert size string to bytes
    def parse_size(size_str):
        size_str = size_str.strip().upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    max_bytes = parse_size(MAX_LOG_SIZE)
    
    # Console handler for internal logs (Docker logs only)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Configure root logger for internal logs (console only)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        handlers=[console_handler],
        force=True
    )
    
    # Suppress Flask HTTP logs unless in DEBUG mode
    if LOG_LEVEL != 'DEBUG':
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.WARNING)
    
    # Create separate logger for notifications (file only, with rotation)
    notifications_logger = logging.getLogger('notifications')
    
    # Configure notifications log format
    if LOG_FORMAT == 'json':
        notifications_format = '%(message)s'  # Just the JSON message
    elif LOG_FORMAT == 'simple':
        notifications_format = '%(asctime)s - %(message)s'  # Keep timestamp for simple
    else:  # detailed
        notifications_format = '%(asctime)s - %(message)s'  # Logger timestamp + our format
    
    # Setup notifications log handler (with rotation, file only)
    if LOG_ROTATION:
        notifications_handler = RotatingFileHandler(
            NOTIFICATIONS_LOG, 
            maxBytes=max_bytes, 
            backupCount=BACKUP_COUNT
        )
    else:
        notifications_handler = logging.FileHandler(NOTIFICATIONS_LOG)
    
    notifications_handler.setFormatter(logging.Formatter(notifications_format))
    notifications_logger.addHandler(notifications_handler)
    notifications_logger.setLevel(logging.INFO)
    
    # Prevent notifications from going to root logger (no console output)
    notifications_logger.propagate = False
    
    return logging.getLogger(__name__), notifications_logger

logger, notifications_logger = setup_logging()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle LoggiFly webhook notifications"""
    try:
        # Get request data
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = request.get_json(silent=True) or {}
        else:
            # Handle plain text or other formats
            raw_data = request.data.decode('utf-8', errors='ignore')
            data = {'message': raw_data}
        
        # Extract LoggiFly data with defaults
        container = data.get('container', 'unknown')
        keyword_raw = data.get('keyword', data.get('keywords', 'unknown'))
        
        # Handle keyword arrays (LoggiFly sometimes sends arrays)
        if isinstance(keyword_raw, list):
            keyword = ', '.join(str(k) for k in keyword_raw)
        else:
            keyword = str(keyword_raw)
            
        # Get message and title from LoggiFly payload
        title = data.get('title', f"LoggiFly: '{keyword}' in {container}")
        message = data.get('message', data.get('body', 'No message'))
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Format log entry based on LOG_FORMAT
        if LOG_FORMAT == 'json':
            log_entry = json.dumps({
                'timestamp': timestamp,
                'container': container,
                'keyword': keyword,
                'title': title,
                'message': message,
                'version': data.get('version', '1.0'),
                'type': data.get('type', 'info')
            })
        elif LOG_FORMAT == 'simple':
            log_entry = f"[{container}] {keyword}: {message}"
        else:  # detailed (default) - clean, readable format
            log_entry = f"{container} | {keyword} | {message}"
        
        # Log to notifications file only (no console spam)
        notifications_logger.info(log_entry)
        
        # Debug log full payload to internal logs if debug level
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Full webhook payload: {json.dumps(data, indent=2)}")
        
        return {'status': 'success', 'message': 'Notification logged'}, 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'status': 'error', 'message': error_msg}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Basic health check - verify notifications log file is writable
        with open(NOTIFICATIONS_LOG, 'a'):
            pass
        return {
            'status': 'healthy',
            'notifications_log': NOTIFICATIONS_LOG,
            'log_level': LOG_LEVEL,
            'version': '1.1'
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
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
        'notifications_log': NOTIFICATIONS_LOG,
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
        
        # Get notification log files
        notifications_size = os.path.getsize(NOTIFICATIONS_LOG) if os.path.exists(NOTIFICATIONS_LOG) else 0
        notifications_pattern = f"{NOTIFICATIONS_LOG}.*"
        notifications_rotated = glob.glob(notifications_pattern)
        
        return {
            'notifications_log': {
                'file': NOTIFICATIONS_LOG,
                'size': notifications_size,
                'rotated_files': len(notifications_rotated),
                'total_files': len(notifications_rotated) + (1 if notifications_size > 0 else 0)
            }
        }, 200
    except Exception as e:
        logger.error(f"Stats check failed: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/icon.png', methods=['GET'])
def icon():
    """Serve the container icon for Unraid"""
    try:
        return send_file('/app/icon.png', mimetype='image/png')
    except Exception as e:
        logger.warning(f"Could not serve icon.png: {e}")
        return {'status': 'error', 'message': str(e)}, 404

if __name__ == '__main__':
    logger.info(f"Starting LoggiFly Helper on {HOST}:{PORT}")
    logger.info(f"Notifications log: {NOTIFICATIONS_LOG}")
    logger.info(f"Log format: {LOG_FORMAT}, level: {LOG_LEVEL}")
    logger.info(f"Log rotation: enabled={LOG_ROTATION}, max_size={MAX_LOG_SIZE}, backups={BACKUP_COUNT}")
    logger.info("Ready to log ALL notifications from LoggiFly")
    
    # Set debug=True for Flask's reloader if LOG_LEVEL is DEBUG
    flask_debug_mode = (LOG_LEVEL == 'DEBUG')
    logger.info(f"Flask debug mode: {flask_debug_mode}")
    
    app.run(host=HOST, port=PORT, debug=flask_debug_mode)