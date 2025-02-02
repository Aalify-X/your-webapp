import sys
import traceback
import json

def log_error(message):
    print(json.dumps({
        "source": "wsgi.py",
        "type": "ERROR",
        "message": str(message)
    }), file=sys.stderr)
    sys.stderr.flush()

try:
    from app import app as application
except Exception as import_error:
    log_error(f"CRITICAL IMPORT ERROR: {import_error}")
    log_error(traceback.format_exc())
    application = None

def handler(event=None, context=None):
    """Vercel serverless function handler"""
    if application is None:
        log_error("Application failed to initialize")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Application initialization failed'})
        }
    
    try:
        # Minimal request handler for Vercel
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Application is running'})
        }
    except Exception as e:
        log_error(f"Handler execution error: {e}")
        log_error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }

# Ensure the handler can be imported
__handler__ = handler
