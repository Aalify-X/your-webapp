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

# Absolute paths for deployment
PROJECT_ROOT = os.environ.get('PROJECT_ROOT', '/opt/render/project/src')
FRONTEND_PATH = os.path.join(PROJECT_ROOT, 'frontend')  # Explicitly point to frontend directory
BACKEND_PATH = os.path.join(PROJECT_ROOT, 'backend')
UPLOAD_FOLDER = os.path.join(BACKEND_PATH, 'uploads')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Logging system configuration
logger.info(f"Project Root: {PROJECT_ROOT}")
logger.info(f"Frontend Path: {FRONTEND_PATH}")
logger.info(f"Backend Path: {BACKEND_PATH}")
logger.info(f"Upload Folder: {UPLOAD_FOLDER}")
logger.info(f"Current Working Directory: {os.getcwd()}")

# Comprehensive file and path diagnostics
def diagnose_project_structure():
    try:
        return {
            'project_root_exists': os.path.exists(PROJECT_ROOT),
            'frontend_path_exists': os.path.exists(FRONTEND_PATH),
            'backend_path_exists': os.path.exists(BACKEND_PATH),
            'upload_folder_exists': os.path.exists(UPLOAD_FOLDER),
            'frontend_files': os.listdir(FRONTEND_PATH) if os.path.exists(FRONTEND_PATH) else [],
            'backend_files': os.listdir(BACKEND_PATH) if os.path.exists(BACKEND_PATH) else []
        }
    except Exception as e:
        return {"error": str(e)}

# Comprehensive path and file discovery function
def find_index_html():
    """
    Systematically search for index.html across multiple potential locations.
    
    Returns:
        str or None: Full path to index.html if found, None otherwise
    """
    search_paths = [
        # Explicitly prioritize frontend directory
        os.path.join(FRONTEND_PATH, 'index.html'),
        
        # Render.com specific paths
        '/opt/render/project/frontend/index.html',
        
        # Relative paths
        os.path.join(os.getcwd(), '..', 'frontend', 'index.html'),
        os.path.join(os.getcwd(), 'frontend', 'index.html'),
        
        # Absolute paths from project root
        os.path.join(PROJECT_ROOT, 'frontend', 'index.html')
    ]
    
    # Log all search paths for diagnostics
    logger.info("Searching for index.html in the following paths:")
    for path in search_paths:
        logger.info(f"Checking path: {path}")
        if os.path.exists(path):
            logger.info(f"Found index.html at: {path}")
            return path
    
    logger.error("Could not find index.html in any of the search paths")
    return None

# Initialize Flask with explicit frontend path
app = Flask(__name__, 
            static_folder=FRONTEND_PATH,  # Explicitly set to frontend directory
            template_folder=FRONTEND_PATH)  # Explicitly set to frontend directory

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)

# Simplified CORS configuration
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Optional CSRF protection
try:
    csrf = CSRFProtect(app)
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

# Home route with comprehensive error handling and path discovery
@app.route('/')
def home():
    try:
        # Attempt to find index.html
        index_path = find_index_html()
        
        if index_path:
            try:
                return render_template(index_path)
            except Exception as render_error:
                logger.error(f"Error rendering {index_path}: {render_error}")
        
        # Fallback diagnostic response
        return jsonify({
            "status": "error",
            "message": "Could not locate or render index.html",
            "project_structure": {
                "search_paths": [
                    '/opt/render/project/src/frontend',
                    '/opt/render/project/frontend',
                    os.path.join(os.getcwd(), '..', 'frontend'),
                    os.path.join(os.getcwd(), 'frontend')
                ],
                "current_directory": os.getcwd(),
                "project_root": PROJECT_ROOT,
                "frontend_path": FRONTEND_PATH,
                "backend_path": BACKEND_PATH
            }
        }), 500
    
    except Exception as e:
        logger.error(f"Comprehensive home route error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": "Unexpected error in home route",
            "error": str(e),
            "project_structure": diagnose_project_structure()
        }), 500

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
            "project_structure": diagnose_project_structure(),
            "environment": os.environ.get('FLASK_ENV', 'Not Set')
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": "Health check failed",
            "error": str(e)
        }), 500

# Ensure debug mode is off in production
app.debug = False

# Use environment-specified port or default
port = int(os.environ.get('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)