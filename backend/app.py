from flask import Flask, session, redirect, url_for, request, jsonify, render_template
from flask_cors import CORS
from auth.routes import auth_bp
from functools import wraps
import os
import PyPDF2
from docx import Document
import requests
import io
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/templates'))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/static'))

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Use a fixed secret key for session persistence
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'NSjUyKL1$8N*@(i')

# Configure session to be permanent
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Session lasts 30 days

# Configure CORS
CORS(app, origins=["https://your-frontend.onrender.com"],
     supports_credentials=True)

# Set up session cookie settings
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access to cookie
    SESSION_COOKIE_SAMESITE='Lax'  # Allow cross-site requests
)

# Set the port for Render
app.config['PORT'] = int(os.getenv('PORT', 10000))

# Register the auth blueprint
app.register_blueprint(auth_bp)

# Error handling
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/digital_planner')
def digital_planner():
    return render_template('digital_planner.html')

@app.route('/whiteboard')
def whiteboard():
    return render_template('whiteboard.html')

@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html')

@app.route('/pdf_tools')
def pdf_tools():
    return render_template('pdf_document_intelligence.html')

# Document processing
@app.route('/api/process_document', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)

    summary_length = int(request.form.get('summary_length', 35))
    question_count = int(request.form.get('question_count', 10))

    try:
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif filename.endswith(('.doc', '.docx')):
            text = extract_text_from_word(file)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        if not text:
            return jsonify({"error": "No readable text in file"}), 400

        summary = generate_summary(text)
        questions = generate_questions(text)

        return jsonify({
            "summary": summary,
            "questions": questions,
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper functions
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    return "".join([page.extract_text() or "" for page in pdf_reader.pages]).strip()

def extract_text_from_word(file):
    doc = Document(io.BytesIO(file.read()))
    return "\n".join([para.text for para in doc.paragraphs])

def query_openrouter(prompt):
    data = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [
            {"role": "system", "content": "You're a helpful AI tutor."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(OPENROUTER_URL, headers=OPENROUTER_HEADERS, json=data)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except requests.exceptions.HTTPError as e:
        print(f"OpenRouter API error: {str(e)}")
        print(f"Response content: {response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def generate_summary(text):
    prompt = f"Write a concise summary of the following text:\n\n{text[:15000]}"
    result = query_openrouter(prompt)
    return result or "Failed to generate summary. Please try again."


def generate_questions(text):
    prompt = f"""Generate important exam-style questions with answers based on the following text.\nFormat each as:\nQ: [question]\nA: [answer]\n\n{text[:15000]}"""
    result = query_openrouter(prompt)
    try:
        with open('llm_questions_raw_output.txt', 'w', encoding='utf-8') as f:
            f.write(repr(result))
    except Exception as log_exc:
        print(f"Failed to write LLM raw output: {log_exc}")
    print('RAW LLM QUESTIONS OUTPUT:', repr(result))

    if not result:
        return [{"question": "Error generating questions", "answer": "Please try again"}]

    questions = []
    current_q = None
    for line in result.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('Q:'):
            if current_q:
                questions.append(current_q)
            q_text = line[2:].strip()
            current_q = {"question": q_text, "answer": ""}
        elif line.startswith('A:') and current_q:
            current_q["answer"] = line[2:].strip()
            questions.append(current_q)
            current_q = None
    if current_q:
        questions.append(current_q)
    return questions

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-frontend.onrender.com",
    "X-Title": "MyAppPDFSummarizer"
}

# Main
if __name__ == '__main__':
    port = app.config['PORT']
    app.run(host='0.0.0.0', port=port)
