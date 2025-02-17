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
import json

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

# Comprehensive filesystem diagnostics
def diagnose_filesystem():
    """
    Perform an exhaustive diagnostic of the filesystem and project structure.
    
    Returns:
        dict: Detailed filesystem and project structure information
    """
    try:
        # Collect comprehensive filesystem information
        filesystem_info = {
            "project_root": {
                "path": PROJECT_ROOT,
                "exists": os.path.exists(PROJECT_ROOT),
                "is_dir": os.path.isdir(PROJECT_ROOT),
                "contents": safe_listdir(PROJECT_ROOT)
            },
            "frontend_path": {
                "path": FRONTEND_PATH,
                "exists": os.path.exists(FRONTEND_PATH),
                "is_dir": os.path.isdir(FRONTEND_PATH),
                "contents": safe_listdir(FRONTEND_PATH)
            },
            "backend_path": {
                "path": BACKEND_PATH,
                "exists": os.path.exists(BACKEND_PATH),
                "is_dir": os.path.isdir(BACKEND_PATH),
                "contents": safe_listdir(BACKEND_PATH)
            },
            "current_working_directory": {
                "path": os.getcwd(),
                "contents": safe_listdir(os.getcwd())
            }
        }
        
        return filesystem_info
    except Exception as e:
        logger.error(f"Error in filesystem diagnosis: {e}")
        return {"error": str(e)}

# Safe directory listing function
def safe_listdir(path):
    """
    Safely list directory contents with error handling.
    
    Args:
        path (str): Directory path to list
    
    Returns:
        list: Directory contents or error information
    """
    try:
        # Attempt to list directory contents
        contents = os.listdir(path)
        
        # Detailed file information
        detailed_contents = []
        for item in contents:
            full_path = os.path.join(path, item)
            try:
                is_dir = os.path.isdir(full_path)
                size = os.path.getsize(full_path) if not is_dir else None
                detailed_contents.append({
                    "name": item,
                    "is_directory": is_dir,
                    "size": size
                })
            except Exception as item_error:
                detailed_contents.append({
                    "name": item,
                    "error": str(item_error)
                })
        
        return detailed_contents
    except Exception as e:
        return [{"error": str(e)}]

# Comprehensive index.html rendering function
def render_index_html():
    """
    Attempt to render index.html with comprehensive error handling and diagnostics.
    
    Returns:
        Flask response or error JSON
    """
    try:
        # Extensive filesystem diagnostics
        filesystem_info = diagnose_filesystem()
        logger.info(f"Filesystem Diagnostics: {json.dumps(filesystem_info, indent=2)}")
        
        # Explicitly check file contents and permissions
        index_path = find_index_html()
        
        if not index_path:
            logger.error("No index.html found in any search path")
            return jsonify({
                "status": "error",
                "message": "index.html not found",
                "filesystem_info": filesystem_info,
                "search_paths": [
                    '/opt/render/project/src/frontend/index.html',
                    os.path.join(os.getcwd(), '..', 'frontend', 'index.html'),
                    os.path.join(PROJECT_ROOT, 'frontend', 'index.html')
                ]
            }), 404
        
        # Detailed file diagnostics
        try:
            with open(index_path, 'r') as f:
                file_contents = f.read()
                logger.info(f"index.html file size: {len(file_contents)} bytes")
                
                # Comprehensive content validation
                if len(file_contents.strip()) == 0:
                    logger.error(f"index.html is empty: {index_path}")
                    return jsonify({
                        "status": "error",
                        "message": "index.html is empty",
                        "file_path": index_path,
                        "filesystem_info": filesystem_info
                    }), 500
        except PermissionError:
            logger.error(f"Permission denied reading {index_path}")
            return jsonify({
                "status": "error", 
                "message": "Cannot read index.html",
                "file_path": index_path,
                "filesystem_info": filesystem_info
            }), 403
        except Exception as read_error:
            logger.error(f"Error reading index.html: {read_error}")
            return jsonify({
                "status": "error",
                "message": f"Error reading index.html: {str(read_error)}",
                "file_path": index_path,
                "filesystem_info": filesystem_info
            }), 500
        
        # Attempt template rendering
        try:
            return render_template(index_path)
        except Exception as render_error:
            logger.error(f"Template rendering error for {index_path}: {render_error}")
            logger.error(traceback.format_exc())
            return jsonify({
                "status": "error",
                "message": "Failed to render index.html",
                "error": str(render_error),
                "file_path": index_path,
                "file_contents": file_contents[:500],  # Partial contents for debugging
                "filesystem_info": filesystem_info
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in index.html rendering: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": "Catastrophic failure rendering index.html",
            "error": str(e),
            "filesystem_info": diagnose_filesystem()
        }), 500

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

# Home route with comprehensive error handling
@app.route('/')
def home():
    return render_index_html()

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