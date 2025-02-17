from flask import Flask, render_template, request, jsonify, session, url_for, flash, redirect
from flask_cors import CORS
from flask_wtf import CSRFProtect
import os
import sys
import time
import base64
from werkzeug.utils import secure_filename
import nltk
from datetime import datetime
import logging
import traceback

# Optional dependencies with fallback
try:
    import PyPDF2
    from pdfminer.high_level import extract_text
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words
    from sumy.parsers.plaintext import PlaintextParser
except ImportError:
    PyPDF2 = None
    extract_text = None
    Tokenizer = None
    LsaSummarizer = None
    Stemmer = None
    get_stop_words = None
    PlaintextParser = None

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app with explicit configurations
app = Flask(__name__, 
            static_folder='../frontend', 
            template_folder='../frontend')

# Simplified CORS configuration
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Optional CSRF protection
try:
    csrf = CSRFProtect(app)
    app.secret_key = os.urandom(24)
except Exception as e:
    logger.warning(f"CSRF protection could not be initialized: {e}")

# Fallback function for missing dependencies
def dependency_fallback(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ImportError as e:
            logger.error(f"Dependency missing for {func.__name__}: {e}")
            return jsonify({
                "status": "error",
                "message": f"Dependency missing: {str(e)}"
            }), 500
    return wrapper

# Health check with comprehensive system information
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        return jsonify({
            "status": "healthy",
            "message": "Backend is running",
            "python_version": sys.version,
            "dependencies": {
                "PyPDF2": bool(PyPDF2),
                "pdfminer": bool(extract_text),
                "sumy": bool(Tokenizer)
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": "Health check failed",
            "error": str(e)
        }), 500

# Preserve existing routes with dependency fallback
@app.route('/')
@dependency_fallback
def home():
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Home route error: {e}")
        return jsonify({
            "status": "error",
            "message": "Could not render home template",
            "error": str(e)
        }), 500

# Ensure debug mode is off in production
app.debug = False

# Add port configuration from environment
port = int(os.environ.get('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)