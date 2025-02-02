import os
import sys
import traceback
import json

# Ensure logging to stderr for Vercel
def log_error(message):
    print(json.dumps({
        "source": "wsgi.py",
        "level": "ERROR",
        "message": str(message)
    }), file=sys.stderr)
    sys.stderr.flush()

try:
    from app import app as application
except Exception as import_error:
    log_error(f"Import Error: {import_error}")
    log_error(traceback.format_exc())
    application = None

def debug_environment():
    """Log all environment variables and system information."""
    log_error("--- ENVIRONMENT DEBUG START ---")
    log_error(f"Python Version: {sys.version}")
    log_error(f"Python Executable: {sys.executable}")
    log_error(f"Current Working Directory: {os.getcwd()}")
    log_error("Environment Variables:")
    for key, value in os.environ.items():
        log_error(f"{key}: {value}")
    log_error("--- ENVIRONMENT DEBUG END ---")

def handle_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions."""
    log_error("Uncaught exception:")
    log_error(traceback.format_exception(exc_type, exc_value, exc_traceback))

# Set the exception handler
sys.excepthook = handle_exception

def main(event=None, context=None):
    debug_environment()
    
    if application is None:
        log_error("Application failed to import")
        raise ImportError("Could not import Flask application")
    
    try:
        return application
    except Exception as e:
        log_error(f"Error in main function: {e}")
        log_error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        debug_environment()
        application.run(debug=False)
    except Exception as e:
        log_error(f"Startup Error: {e}")
        log_error(traceback.format_exc())
