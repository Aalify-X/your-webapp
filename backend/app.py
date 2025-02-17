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
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diagnostic function to log system paths
def log_system_paths():
    paths = {
        'Current Working Directory': os.getcwd(),
        'Python Path': sys.path,
        'Project Root': os.environ.get('PROJECT_ROOT', 'Not Set'),
        'Possible Frontend Paths': [
            '/opt/render/project/src/frontend',
            '/opt/render/project/frontend',
            '../frontend',
            'frontend'
        ]
    }
    
    for key, value in paths.items():
        logger.info(f"{key}: {value}")

# Log system paths at startup
log_system_paths()

# Determine the most likely frontend path
def find_frontend_path():
    possible_paths = [
        '/opt/render/project/src/frontend',
        '/opt/render/project/frontend',
        os.path.abspath('../frontend'),
        os.path.abspath('frontend')
    ]
    
    for path in possible_paths:
        index_path = os.path.join(path, 'index.html')
        if os.path.exists(index_path):
            logger.info(f"Found frontend path: {path}")
            return path
    
    logger.error("Could not find frontend path")
    return None

# Initialize Flask with flexible path detection
frontend_path = find_frontend_path()
app = Flask(__name__, 
            static_folder=frontend_path, 
            template_folder=frontend_path)

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
            },
            "frontend_path": frontend_path,
            "environment": os.environ.get('FLASK_ENV', 'Not Set')
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": "Health check failed",
            "error": str(e)
        }), 500

# Home route with comprehensive error handling
@app.route('/')
@dependency_fallback
def home():
    try:
        if frontend_path:
            index_path = os.path.join(frontend_path, 'index.html')
            if os.path.exists(index_path):
                return render_template(index_path)
        
        # Fallback error response
        return jsonify({
            "status": "error",
            "message": "Could not locate frontend template",
            "frontend_path": frontend_path
        }), 500
    
    except Exception as e:
        logger.error(f"Comprehensive home route error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": "Template rendering failed",
            "error": str(e),
            "frontend_path": frontend_path
        }), 500

# Ensure debug information is logged
logger.info(f"Static folder: {app.static_folder}")
logger.info(f"Template folder: {app.template_folder}")

# Ensure static and template paths are correctly set
app.static_folder = app.static_folder
app.template_folder = app.template_folder

# Ensure debug mode is off in production
app.debug = False

# Add port configuration from environment
port = int(os.environ.get('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)