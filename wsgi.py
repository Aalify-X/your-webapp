import sys
import traceback
from app import app as application

def handle_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions."""
    print("Uncaught exception:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    sys.stderr.flush()

# Set the exception handler
sys.excepthook = handle_exception

def main(event=None, context=None):
    try:
        return application
    except Exception as e:
        print(f"Error in main function: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise

if __name__ == "__main__":
    application.run(debug=False)
