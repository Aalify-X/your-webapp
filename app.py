from flask import Flask, render_template, request, jsonify, session
import os
import time
import base64
from werkzeug.utils import secure_filename
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import re

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Create Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(os.path.join(UPLOAD_FOLDER, 'pdf'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'whiteboard'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_default_theme():
    return {
        'banner_color': '#FFB6C1',
        'background_color': '#FFF5F5',
        'button_color': '#FF69B4',
        'text_color': '#333333'
    }

@app.before_request
def before_request():
    # Initialize theme data if not present
    if 'theme_data' not in session:
        session['theme_data'] = get_default_theme()

@app.route('/')
def index():
    return render_template('index.html', theme_data=session.get('theme_data', get_default_theme()))

@app.route('/pdf_summary')
def pdf_summary():
    return render_template('pdf_summary.html', theme_data=session.get('theme_data', get_default_theme()))

@app.route('/whiteboard_view')
def whiteboard_view():
    return render_template('whiteboard.html', theme_data=session.get('theme_data', get_default_theme()))

@app.route('/flashcards')
def flashcards_view():
    return render_template('flashcards.html', theme_data=session.get('theme_data', get_default_theme()))

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'pdf', filename)
            file.save(filepath)
            
            # Extract text from PDF
            text = extract_text_from_pdf(filepath)
            
            # Simple processing: split into sentences
            sentences = nltk.sent_tokenize(text)
            
            # Get the requested number of points
            num_points = min(int(request.form.get('num_points', 30)), 50)
            summary_points = sentences[:num_points]
            
            # Generate simple questions
            questions = [
                f"What is the main point of: {sent}?"
                for sent in sentences[:5]
            ]
            
            # Clean up
            try:
                os.remove(filepath)
            except:
                pass
            
            return render_template('pdf_result.html',
                                summary=summary_points,
                                questions=questions,
                                filename=filename)
    except Exception as e:
        return str(e), 500

@app.route('/create_flashcard', methods=['POST'])
def create_flashcard():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        front = data.get('front')
        back = data.get('back')
        
        if not front or not back:
            return jsonify({'error': 'Front and back are required'}), 400
            
        if 'flashcards' not in session:
            session['flashcards'] = []
            
        session['flashcards'].append({
            'front': front,
            'back': back
        })
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'flashcard': {'front': front, 'back': back}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_flashcards')
def get_flashcards():
    return jsonify(session.get('flashcards', []))

@app.route('/delete_flashcard', methods=['POST'])
def delete_flashcard():
    try:
        data = request.get_json()
        index = data.get('index')
        
        if 'flashcards' in session and 0 <= index < len(session['flashcards']):
            session['flashcards'].pop(index)
            session.modified = True
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Flashcard not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/study_planner')
def study_planner():
    return render_template('study_planner.html', theme_data=session.get('theme_data', get_default_theme()))

@app.route('/save_task', methods=['POST'])
def save_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'tasks' not in session:
            session['tasks'] = []
            
        session['tasks'].append({
            'day': data.get('day'),
            'time': data.get('time'),
            'description': data.get('description'),
            'priority': data.get('priority', 'medium')
        })
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'tasks': session['tasks']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_tasks')
def get_tasks():
    return jsonify(session.get('tasks', []))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    try:
        data = request.get_json()
        index = data.get('index')
        
        if 'tasks' in session and 0 <= index < len(session['tasks']):
            session['tasks'].pop(index)
            session.modified = True
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_plans')
def get_plans():
    return jsonify(session.get('study_plans', []))

@app.route('/delete_plan', methods=['POST'])
def delete_plan():
    try:
        data = request.get_json()
        index = data.get('index')
        
        if 'study_plans' in session and 0 <= index < len(session['study_plans']):
            session['study_plans'].pop(index)
            session.modified = True
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Plan not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/get_current_theme')
def get_current_theme():
    return jsonify(session.get('theme_data', get_default_theme()))

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if 'schedule' not in session:
            session['schedule'] = {}
            
        day = data.get('day')
        row = data.get('row')
        tasks = data.get('tasks')
        
        if not all([day, isinstance(row, int), tasks]):
            return jsonify({'error': 'Invalid data format'}), 400
            
        if day not in session['schedule']:
            session['schedule'][day] = {}
            
        session['schedule'][day][str(row)] = tasks
        session.modified = True
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_schedule')
def get_schedule():
    return jsonify(session.get('schedule', {}))

@app.route('/delete_schedule_item', methods=['POST'])
def delete_schedule_item():
    try:
        data = request.get_json()
        index = data.get('index')
        
        if 'schedule' in session and 0 <= index < len(session['schedule']):
            session['schedule'].pop(index)
            session.modified = True
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Schedule item not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    pdf_file = request.files['pdf_file']
    if pdf_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if pdf_file and allowed_file(pdf_file.filename):
        try:
            # Your existing PDF processing code...
            return render_template('pdf_summary.html', 
                                summary=summary, 
                                filename=pdf_file.filename,
                                theme_data=session.get('theme_data', get_default_theme()))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    try:
        # Your existing summary generation code...
        return render_template('pdf_summary.html', 
                            summary=summary,
                            theme_data=session.get('theme_data', get_default_theme()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()