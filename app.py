from flask import Flask, render_template, request, jsonify, session, url_for, flash, redirect
from flask_wtf import CSRFProtect
from flask_mail import Mail, Message
import os
import time
import base64
from werkzeug.utils import secure_filename
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import re
import pyotp
import random
import string
import json
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# Configure port and server settings
app.config['PORT'] = int(os.getenv('PORT', 8080))  # Use 8080 as default
app.config['SERVER_NAME'] = os.getenv('SERVER_NAME', 'localhost')  # Remove port from server name
app.config['PREFERRED_URL_SCHEME'] = 'https' if os.getenv('ENVIRONMENT', 'development') == 'production' else 'http'

# Configure logging
app.logger.setLevel(logging.DEBUG)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = bool(os.getenv('MAIL_USE_TLS', True))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# Configure session settings
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Optional PDF processing module
pdfminer_available = False
try:
    from pdfminer.high_level import extract_text
    pdfminer_available = True
except ImportError:
    print("pdfminer not available")

# Try to import transformers if available
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="t5-small")
except ImportError as e:
    print(f"Could not import transformers: {e}")
    summarizer = None
except Exception as e:
    print(f"Error initializing summarizer: {e}")
    summarizer = None

# Download necessary NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    print(f"Could not download NLTK resources: {e}")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper Functions
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        raise ValueError("Email credentials not configured properly")
        
    msg = Message('Your OTP for Progrify',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f"Your one-time password (OTP) is: {otp}\nThis OTP will expire in 5 minutes."
    
    try:
        mail.send(msg)
        app.logger.info(f"Email sent successfully to {email}")
        return True
    except Exception as e:
        app.logger.error(f"Error sending email to {email}: {str(e)}")
        raise

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_text(pdf_path):
    try:
        reader = PyPDF2.PdfReader(open(pdf_path, 'rb'))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def get_default_theme():
    return {
        "primary_color": "#3498db",
        "secondary_color": "#2ecc71",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "font_family": "Arial, sans-serif"
    }

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email', 'error')
            return render_template('index.html', show_otp_form=False)
        
        # Generate OTP
        otp = generate_otp()
        session['otp'] = otp
        session['otp_generated_at'] = datetime.now().timestamp()
        session['user_email'] = email

        # Send OTP
        try:
            send_otp_email(email, otp)
            flash('OTP sent to your email. Please check your inbox.', 'success')
            return render_template('index.html', show_otp_form=True, email=email)
        except Exception as e:
            flash(f'Failed to send OTP: {str(e)}. Please try again later.', 'error')
            return render_template('index.html', show_otp_form=False)

    # Clear OTP-related session when accessing login page directly
    session.pop('otp', None)
    session.pop('otp_generated_at', None)
    return render_template('index.html', show_otp_form=False)

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    if 'user_email' not in session:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))

    entered_otp = request.form.get('otp')
    stored_otp = session.get('otp')
    
    if not entered_otp:
        flash('Please enter the OTP', 'error')
        return render_template('index.html', show_otp_form=True, email=session.get('user_email'))

    if not stored_otp:
        flash('No OTP generated. Please request a new OTP.', 'error')
        return redirect(url_for('login'))

    # Check OTP expiration (5 minutes)
    if datetime.now().timestamp() - session.get('otp_generated_at', 0) > 300:
        flash('OTP has expired. Please request a new OTP.', 'error')
        return redirect(url_for('login'))

    if entered_otp == stored_otp:
        # Clear OTP related session data
        session.pop('otp', None)
        session.pop('otp_generated_at', None)
        
        # Mark user as logged in
        session['logged_in'] = True
        
        flash('Successfully logged in!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Invalid OTP. Please try again.', 'error')
        return render_template('index.html', show_otp_form=True, email=session.get('user_email'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('index.html', theme_data=session.get('theme_data', get_default_theme()))


# Download necessary NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    print(f"Could not download NLTK resources: {e}")

# Optional NLP imports with fallbacks
summarizer = None
question_generator = None

# Try to import transformers if available
try:
    from transformers import pipeline
    summarizer = pipeline("summarization", model="t5-small")
except ImportError:
    print("Transformers not available")

# Fallback functions for text processing
def extract_key_topics_fallback(text, top_n=3):
    """Extract key topics using basic NLTK processing with reduced complexity."""
    try:
        import nltk
        from collections import Counter
        
        # Tokenize with minimal processing
        words = nltk.word_tokenize(text.lower())
        words = [word for word in words if word.isalnum()]
        
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(top_n)]
    except Exception as e:
        print(f"Error in extract_key_topics: {e}")
        return []

def fallback_summarize(text, num_lines=3):
    """Simple extractive summarization if no ML model is available."""
    try:
        import nltk
        sentences = nltk.sent_tokenize(text)
        return '. '.join(sentences[:num_lines]) + '.'
    except Exception as e:
        print(f"Error in fallback summarization: {e}")
        return text[:500]  # Return first 500 characters as a fallback

def fallback_generate_questions(text, num_questions=2):
    """Generate basic questions if no ML model is available."""
    sentences = sent_tokenize(text)
    return [f"What is the main point of: {sent}?" for sent in sentences[:num_questions]]

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Summarization pipeline using HuggingFace Transformers
# summarizer = pipeline("summarization", model="t5-small")

# Function to check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF file using PyPDF2.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text from the PDF
    """
    try:
        reader = PyPDF2.PdfReader(open(pdf_path, 'rb'))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

# Route to upload and process the PDF
@app.route('/upload_pdf', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    # Implement more memory-efficient file handling
    try:
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400
        
        # Save file temporarily and process in chunks
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process file with memory-efficient method
        if pdfminer_available:
            text = extract_text(filepath)
        else:
            text = extract_pdf_text(filepath)
        
        # Clean up temporary file
        os.remove(filepath)
        
        return jsonify({"text": text[:2000]})  # Limit text size
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to display the summarized text and generate flashcards
@app.route('/generate_flashcards', methods=['GET'])
@login_required
def generate_flashcards():
    summarized_text = session.get('summarized_text')
    
    if summarized_text:
        # Here, you can implement flashcard generation logic from the summarized text
        # For now, we're just displaying the summarized text
        flashcards = [summarized_text]  # Replace with actual flashcard generation logic
        
        return render_template('flashcards.html', flashcards=flashcards)
    
    flash("No summarized text available. Please upload and process a PDF first.")
    return redirect(url_for('upload_pdf'))

# Route to display uploaded PDF and its summary (for testing)
@app.route('/pdf_document_intelligence')
@login_required
def pdf_document_intelligence():
    return render_template('pdf_document_intelligence.html')

@app.route('/create_flashcard', methods=['POST'])
@login_required
def create_flashcard():
    try:
        data = request.get_json()
        front = data.get('front')
        back = data.get('back')

        if not front or not back:
            return jsonify({
                'status': 'error', 
                'error': 'Front and back are required'
            }), 400

        # Ensure session has flashcards list
        if 'flashcards' not in session:
            session['flashcards'] = []

        # Create unique ID for the flashcard
        new_flashcard = {
            'id': len(session['flashcards']) + 1,
            'front': front,
            'back': back,
            'created_at': datetime.now().isoformat()
        }

        session['flashcards'].append(new_flashcard)
        session.modified = True

        return jsonify({
            'status': 'success',
            'flashcard': new_flashcard
        }), 200

    except Exception as e:
        app.logger.error(f"Flashcard creation error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/get_flashcards')
@login_required
def get_flashcards():
    flashcards = session.get('flashcards', [])
    return jsonify({
        'status': 'success',
        'flashcards': flashcards
    })

@app.route('/delete_flashcard', methods=['POST'])
@login_required
def delete_flashcard():
    try:
        data = request.get_json()
        card_id = data.get('id')

        if not card_id:
            return jsonify({
                'status': 'error', 
                'error': 'Card ID is required'
            }), 400

        # Find and remove the flashcard
        session['flashcards'] = [
            card for card in session.get('flashcards', []) 
            if card['id'] != card_id
        ]
        session.modified = True

        return jsonify({
            'status': 'success',
            'message': 'Flashcard deleted successfully'
        }), 200

    except Exception as e:
        app.logger.error(f"Flashcard deletion error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/save_whiteboard', methods=['POST'])
@login_required
def save_whiteboard():
    try:
        data = request.get_json()
        if not data or 'imageData' not in data:
            return jsonify({'error': 'No image data provided'}), 400
            
        whiteboard_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'whiteboard')
        os.makedirs(whiteboard_dir, exist_ok=True)
        
        image_data = data['imageData'].split(',')[1]
        filename = f'whiteboard_{int(time.time())}.png'
        filepath = os.path.join(whiteboard_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
            
        return jsonify({
            'success': True,
            'filepath': filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_whiteboards')
@login_required
def get_whiteboards():
    try:
        whiteboard_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'whiteboard')
        files = []
        if os.path.exists(whiteboard_dir):
            files = [f for f in os.listdir(whiteboard_dir) if f.startswith('whiteboard_')]
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_current_theme')
@login_required
def get_current_theme():
    theme_data = session.get('theme_data', get_default_theme())
    return jsonify(theme_data)

@app.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    themes = {
        'pastel_pink': {
            'banner_color': '#FFB6C1',
            'background_color': '#FFCFB35F5',
            'button_color': '#FF69B4',
            'text_color': '#333333'
        },
        'pastel_blue': {
            'banner_color': '#B6D0E2',
            'background_color': '#F0F8FF',
            'button_color': '#89CFF0',
            'text_color': '#333333'
        },
        'pastel_green': {
            'banner_color': '#98FB98',
            'background_color': '#F0FFCFB30',
            'button_color': '#90EE90',
            'text_color': '#333333'
        },
        'lavender': {
            'banner_color': '#E6E6FA',
            'background_color': '#F5EFFCFB3',
            'button_color': '#9B7EDE',
            'text_color': '#333333'
        }
    }
    
    try:
        data = request.get_json()
        theme_name = data.get('theme')
        
        if theme_name in themes:
            session['theme_data'] = themes[theme_name]
            return jsonify({'status': 'success', 'theme': themes[theme_name]})
        return jsonify({'error': 'Invalid theme'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress_tracking', methods=['GET', 'POST'])
@login_required
def progress_tracking():
    if request.method == 'POST':
        try:
            data = request.get_json()
            action = data.get('action')
            
            if action == 'add_goal':
                goal = {
                    'title': data.get('title'),
                    'description': data.get('description'),
                    'target_date': data.get('target_date'),
                    'status': 'In Progress'
                }
                
                if 'goals' not in session:
                    session['goals'] = []
                
                session['goals'].append(goal)
                session.modified = True
                
                return jsonify({
                    'status': 'success',
                    'goal': goal
                })
            
            elif action == 'update_goal':
                goals = session.get('goals', [])
                goal_index = data.get('index')
                
                if goal_index is not None and 0 <= goal_index < len(goals):
                    goals[goal_index]['status'] = data.get('status', goals[goal_index]['status'])
                    session.modified = True
                    
                    return jsonify({
                        'status': 'success',
                        'goal': goals[goal_index]
                    })
                
                return jsonify({'error': 'Invalid goal index'}), 400
            
            return jsonify({'error': 'Invalid action'}), 400
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request renders the template with existing goals
    return render_template('progress_tracking.html', 
                           theme_data=session.get('theme_data', get_default_theme()),
                           goals=session.get('goals', []))

@app.route('/delete_pdf', methods=['POST'])
@login_required
def delete_pdf():
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'status': 'error', 'error': 'No filename provided'}), 400
        
        # Ensure filename is secure and within the PDF upload directory
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf', filename)
        
        # Check if file exists before attempting to delete
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remove from session's uploaded PDFs
        if 'uploaded_pdfs' in session:
            session['uploaded_pdfs'] = [
                pdf for pdf in session['uploaded_pdfs'] 
                if pdf['filename'] != filename
            ]
            session.modified = True
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/save_goal', methods=['POST'])
@login_required
def save_goal():
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({'status': 'error', 'error': 'No data provided'}), 400
        
        title = data.get('title')
        description = data.get('description')
        goal_type = data.get('type')
        deadline = data.get('deadline')
        
        if not title or not goal_type:
            return jsonify({'status': 'error', 'error': 'Title and type are required'}), 400
        
        # Initialize goals in session if not exists
        if 'goals' not in session:
            session['goals'] = []
        
        # Create goal object
        goal = {
            'id': str(len(session['goals']) + 1),
            'title': title,
            'description': description or '',
            'type': goal_type,
            'deadline': deadline or ''
        }
        
        # Add goal to session
        session['goals'].append(goal)
        session.modified = True
        
        return jsonify({
            'status': 'success', 
            'goal': goal
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/get_goals')
@login_required
def get_goals():
    try:
        goals = session.get('goals', [])
        return jsonify({
            'status': 'success',
            'goals': goals
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/delete_goal', methods=['POST'])
@login_required
def delete_goal():
    try:
        data = request.get_json()
        goal_id = data.get('goal_id')
        
        if not goal_id:
            return jsonify({
                'status': 'error', 
                'error': 'No goal ID provided'
            }), 400
        
        if 'goals' not in session:
            return jsonify({
                'status': 'error', 
                'error': 'No goals found'
            }), 400
        
        session['goals'] = [goal for goal in session['goals'] if goal['id'] != goal_id]
        session.modified = True
        
        return jsonify({
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/save_schedule', methods=['POST'])
@login_required
def save_schedule():
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({
                'status': 'error', 
                'error': 'No data provided'
            }), 400
        
        title = data.get('title')
        day = data.get('day')
        time = data.get('time')
        
        if not title or not day or not time:
            return jsonify({
                'status': 'error', 
                'error': 'Title, day, and time are required'
            }), 400
        
        # Initialize schedule in session if not exists
        if 'schedule' not in session:
            session['schedule'] = []
        
        # Create schedule item
        schedule_item = {
            'id': str(len(session['schedule']) + 1),
            'title': title,
            'day': day,
            'time': time
        }
        
        # Add schedule item to session
        session['schedule'].append(schedule_item)
        session.modified = True
        
        return jsonify({
            'status': 'success', 
            'schedule_item': schedule_item
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/get_schedule')
@login_required
def get_schedule():
    try:
        schedule = session.get('schedule', [])
        return jsonify({
            'status': 'success',
            'schedule': schedule
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/delete_schedule', methods=['POST'])
@login_required
def delete_schedule():
    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')
        
        if not schedule_id:
            return jsonify({
                'status': 'error', 
                'error': 'No schedule ID provided'
            }), 400
        
        if 'schedule' not in session:
            return jsonify({
                'status': 'error', 
                'error': 'No schedule found'
            }), 400
        
        session['schedule'] = [
            item for item in session['schedule'] 
            if item['id'] != schedule_id
        ]
        session.modified = True
        
        return jsonify({
            'status': 'success'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/update_goal', methods=['POST'])
@login_required
def update_goal():
    try:
        data = request.get_json()
        goal_id = data.get('goal_id')
        status = data.get('status')

        if not goal_id or not status:
            return jsonify({
                'status': 'error', 
                'error': 'Goal ID and status are required'
            }), 400

        if 'goals' not in session:
            return jsonify({
                'status': 'error', 
                'error': 'No goals found'
            }), 400

        for goal in session['goals']:
            if goal['id'] == goal_id:
                goal['status'] = status
                session.modified = True
                return jsonify({
                    'status': 'success', 
                    'goal': goal
                }), 200

        return jsonify({
            'status': 'error', 
            'error': 'Goal not found'
        }), 404

    except Exception as e:
        app.logger.error(f"Goal update error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/dashboard')
@login_required
def dashboard():
    theme_data = session.get('theme_data', get_default_theme())
    
    # Aggregate data from different sections
    dashboard_data = {
        'flashcards_count': len(session.get('flashcards', [])),
        'uploaded_pdfs_count': len(session.get('uploaded_pdfs', [])),
        'goals_count': len(session.get('goals', [])),
        'active_challenges': session.get('active_challenges', [])
    }
    
    return render_template('dashboard.html', 
                           theme_data=theme_data, 
                           dashboard_data=dashboard_data)

def get_default_theme():
    """
    Returns a default theme configuration for the application.
    
    Returns:
        dict: A dictionary containing default theme settings.
    """
    return {
        "primary_color": "#3498db",  # Blue
        "secondary_color": "#2ecc71",  # Green
        "text_color": "#333333",  # Dark gray
        "background_color": "#FFCFB3FFCFB3",  # White
        "font_family": "Arial, sans-serif"
    }

@app.route('/flashcards')
@login_required
def flashcards():
    theme_data = get_default_theme()
    return render_template('flashcards.html', theme_data=theme_data)

@app.route('/whiteboard_view')
@login_required
def whiteboard():
    theme_data = get_default_theme()
    return render_template('whiteboard.html', theme_data=theme_data)

@app.route('/digital_planner')
@login_required
def digital_planner():
    theme_data = get_default_theme()
    return render_template('digital_planner.html', theme_data=theme_data)

# Error handling
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    # For local development only
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

