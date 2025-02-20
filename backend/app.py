from flask import Flask, render_template, request, jsonify, session, url_for, flash, redirect
from flask_wtf import CSRFProtect
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
from pdfminer.high_level import extract_text
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from sumy.parsers.plaintext import PlaintextParser
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Add CSRF protection
csrf = CSRFProtect(app)
app.secret_key = os.urandom(24)

# Add a simple route for testing
@app.route("/")
def home():
    return render_template("index.html")

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
    try:
        summarizer = pipeline("summarization", model="t5-small")
        question_generator = pipeline("text2text-generation", model="t5-small")
    except Exception as e:
        print(f"Transformers pipeline loading failed: {e}")
except ImportError:
    print("Transformers not available. Using fallback text processing methods.")

# Fallback functions for text processing
def extract_key_topics_fallback(text, top_n=5):
    """Extract key topics using basic NLTK processing."""
    try:
        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        word_freq = Counter(filtered_words)
        return [word for word, _ in word_freq.most_common(top_n)]
    except Exception as e:
        print(f"Error in extract_key_topics: {e}")
        return []

def fallback_summarize(text, num_lines=3):
    """Simple extractive summarization if no ML model is available."""
    sentences = sent_tokenize(text)
    return '. '.join(sentences[:num_lines]) + '.'

def fallback_generate_questions(text, num_questions=2):
    """Generate basic questions if no ML model is available."""
    sentences = sent_tokenize(text)
    return [f"What is the main point of: {sent}?" for sent in sentences[:num_questions]]

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Summarization pipeline using HuggingFace Transformers
summarizer = pipeline("summarization", model="t5-small")

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
def upload_pdf():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash("No file part")
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash("No selected file")
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Save the uploaded PDF file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text from PDF
            text = extract_pdf_text(filepath)
            
            if text:
                # Summarize the extracted text
                summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
                summarized_text = summary[0]['summary_text']
                
                # Save the summarized text in the session for later use
                session['summarized_text'] = summarized_text
                flash("PDF processed and summarized successfully!")
                
                return render_template('summarized_text.html', summarized_text=summarized_text)
            else:
                flash("Failed to extract text from PDF")
                return redirect(request.url)
        
        else:
            flash("Invalid file type. Please upload a PDF file.")
            return redirect(request.url)
    
    return render_template('upload_pdf.html')

# Route to display the summarized text and generate flashcards
@app.route('/generate_flashcards', methods=['GET'])
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
def pdf_document_intelligence():
    return render_template('pdf_document_intelligence.html')


@app.route('/create_flashcard', methods=['POST'])
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
def get_flashcards():
    flashcards = session.get('flashcards', [])
    return jsonify({
        'status': 'success',
        'flashcards': flashcards
    })

@app.route('/delete_flashcard', methods=['POST'])
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
def get_current_theme():
    theme_data = session.get('theme_data', get_default_theme())
    return jsonify(theme_data)

@app.route('/update_theme', methods=['POST'])
def update_theme():
    themes = {
        'pastel_pink': {
            'banner_color': '#FFB6C1',
            'background_color': '#FFF5F5',
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
            'background_color': '#F0FFF0',
            'button_color': '#90EE90',
            'text_color': '#333333'
        },
        'lavender': {
            'banner_color': '#E6E6FA',
            'background_color': '#F5EFFF',
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
        "background_color": "#ffffff",  # White
        "font_family": "Arial, sans-serif"
    }

@app.route('/')
def index():
    theme_data = get_default_theme()
    return render_template('index.html', theme_data=theme_data)

# Routes for main features
@app.route('/flashcards')
def flashcards():
    theme_data = get_default_theme()
    return render_template('flashcards.html', theme_data=theme_data)

@app.route('/whiteboard_view')
def whiteboard():
    theme_data = get_default_theme()
    return render_template('whiteboard.html', theme_data=theme_data)

@app.route('/digital_planner')
def digital_planner():
    theme_data = get_default_theme()
    return render_template('digital_planner.html', theme_data=theme_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Run the Flask app on port 5000