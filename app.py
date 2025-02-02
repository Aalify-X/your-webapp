from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, g
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import logging
import sys
import base64
import time
from dotenv import load_dotenv
import secrets
import traceback

# Load environment variables
load_dotenv()

# Configure logging
def log_error(message):
    print(message, file=sys.stderr)
    sys.stderr.flush()

logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_folder='static', 
            template_folder='templates')

# Generate or retrieve secret key
def get_secret_key():
    # Try to get from environment variable
    secret_key = os.getenv('SECRET_KEY')
    
    # If not set, generate a secure random key
    if not secret_key:
        logger.warning("No SECRET_KEY found. Generating a new one.")
        secret_key = secrets.token_hex(32)
    
    return secret_key

# Configure app using environment variables
app.config['SECRET_KEY'] = get_secret_key()
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  

def ensure_upload_directories():
    """Ensure upload directory exists."""
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception as e:
        log_error(f"Error creating upload directory: {e}")
        log_error(traceback.format_exc())

ensure_upload_directories()

@app.route('/')
def index():
    try:
        theme_data = session.get('theme_data', {
            'banner_color': '#FFB6C1',
            'background_color': '#FFF5F5',
            'button_color': '#FF69B4'
        })
        return render_template('index.html', theme_data=theme_data)
    except Exception as e:
        log_error(f"Error in index route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/pdf_summary', methods=['GET'])
def pdf_summary():
    """
    Render the PDF summary page.
    """
    try:
        return render_template('pdf_summary.html')
    except Exception as e:
        log_error(f"Error in pdf_summary route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/process_pdf', methods=['POST'])
def pdf_summary_post():
    """
    Handle PDF summary generation with comprehensive error handling.
    Supports multiple input formats and provides detailed error responses.
    """
    try:
        # Check for file in multiple possible locations
        file = None
        if 'file' in request.files:
            file = request.files['file']
        elif 'pdf' in request.files:
            file = request.files['pdf']
        
        if file is None:
            return jsonify({
                'error': 'No PDF file found in request',
                'details': 'Please upload a valid PDF file',
                'status': 400
            }), 400
        
        # Validate filename
        if file.filename == '':
            return jsonify({
                'error': 'No selected file',
                'details': 'The uploaded file has no filename',
                'status': 400
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type',
                'details': 'Only PDF files are allowed',
                'status': 400
            }), 400
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf', filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Process PDF
        result = process_pdf(filepath)
        
        # Clean up temporary file after processing
        try:
            os.remove(filepath)
        except Exception as cleanup_error:
            log_error(f"Could not delete temporary PDF file: {cleanup_error}")
            log_error(traceback.format_exc())
        
        if result['success']:
            return jsonify({
                'summary_points': result['summary_points'],
                'questions': result['questions'],
                'file_name': result['file_name'],
                'text_length': result.get('text_length', 0),
                'status': 200
            }), 200
        else:
            return jsonify({
                'error': 'PDF Processing Failed',
                'details': result.get('error', 'Unknown processing error'),
                'status': 500
            }), 500
    
    except json.JSONDecodeError:
        return jsonify({
            'error': 'Invalid JSON',
            'details': 'The request body is not a valid JSON',
            'status': 400
        }), 400
    
    except Exception as e:
        log_error(f"Unexpected error in PDF summary: {e}")
        log_error(traceback.format_exc())
        return jsonify({
            'error': 'Internal Server Error',
            'details': str(e),
            'status': 500
        }), 500

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF file upload with proper error handling."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf', filename)
        
        try:
            file.save(filepath)
        except Exception as e:
            log_error(f"Error saving file: {e}")
            log_error(traceback.format_exc())
            return jsonify({'error': f'Error saving file: {str(e)}'}), 500
            
        return jsonify({'success': True, 'filepath': filepath})
        
    except Exception as e:
        log_error(f"Server error: {e}")
        log_error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/upload_whiteboard_image', methods=['POST'])
def upload_whiteboard_image():
    """Handle whiteboard image upload with proper error handling."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg, gif'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'whiteboard_images', filename)
        
        try:
            file.save(filepath)
        except Exception as e:
            log_error(f"Error saving image: {e}")
            log_error(traceback.format_exc())
            return jsonify({'error': f'Error saving image: {str(e)}'}), 500
            
        return jsonify({'success': True, 'filepath': filepath})
        
    except Exception as e:
        log_error(f"Server error: {e}")
        log_error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/flashcards', methods=['GET', 'POST'])
def flashcards_view():
    try:
        theme_data = session.get('theme_data', {
            'banner_color': '#FFB6C1',
            'background_color': '#FFF5F5',
            'button_color': '#FF69B4'
        })
        if 'flashcards' not in session:
            session['flashcards'] = []
            
        if request.method == 'POST':
            front = request.form.get('front')
            back = request.form.get('back')
            
            if front and back:  # Only add if both fields are filled
                session['flashcards'] = session.get('flashcards', []) + [{
                    'front': front,
                    'back': back
                }]
                
                # Save the updated flashcards list to session
                session.modified = True
                
                return jsonify({
                    'status': 'success',
                    'message': 'Flashcard created successfully',
                    'flashcard': {'front': front, 'back': back}
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Both front and back are required'
                }), 400
                
        return render_template('flashcards.html', 
                             flashcards=session.get('flashcards', []), theme_data=theme_data)
    except Exception as e:
        log_error(f"Error in flashcards route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/delete_flashcard/<int:index>', methods=['POST'])
def delete_flashcard(index):
    try:
        if 'flashcards' in session and 0 <= index < len(session['flashcards']):
            session['flashcards'].pop(index)
            session.modified = True
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error'}), 404
    except Exception as e:
        log_error(f"Error in delete_flashcard route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/study_planner', methods=['GET', 'POST'])
def study_planner_view():
    try:
        theme_data = session.get('theme_data', {
            'banner_color': '#FFB6C1',
            'background_color': '#FFF5F5',
            'button_color': '#FF69B4'
        })
        if request.method == 'POST':
            session['study_plan'] = request.form.get('study_plan')
        return render_template('study_planner.html', theme_data=theme_data)
    except Exception as e:
        log_error(f"Error in study_planner route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/advanced_notes')
def advanced_notes():
    try:
        return redirect(url_for('whiteboard'))
    except Exception as e:
        log_error(f"Error in advanced_notes route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/whiteboard')
def whiteboard():
    try:
        theme_data = session.get('theme_data', {
            'banner_color': '#FFB6C1',
            'background_color': '#FFF5F5',
            'button_color': '#FF69B4'
        })
        """Render the whiteboard page."""
        return render_template('whiteboard.html', theme_data=theme_data)
    except Exception as e:
        log_error(f"Error in whiteboard route: {e}")
        log_error(traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/whiteboard/save', methods=['POST'])
def save_whiteboard():
    """Save the whiteboard state."""
    try:
        data = request.json
        if not data or 'imageData' not in data:
            return jsonify({'success': False, 'error': 'No data provided'})
            
        # Generate a unique filename
        filename = f'whiteboard_{int(time.time())}.png'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'whiteboard_images', filename)
        
        # Save the image data
        image_data = data['imageData'].split(',')[1]  # Remove the data URL prefix
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
            
        return jsonify({
            'success': True,
            'url': url_for('static', filename=f'uploads/whiteboard_images/{filename}')
        })
    except Exception as e:
        log_error(f"Error saving whiteboard: {e}")
        log_error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    log_error(f"404 error: {error}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    log_error(f"500 error: {error}")
    log_error(traceback.format_exc())
    return render_template('500.html'), 500

# Catch any unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    log_error(f"Unhandled exception: {e}")
    log_error(traceback.format_exc())
    return jsonify({"error": "Unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=False)