import os
from flask import Flask, session, redirect, url_for, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

# Set template and static directories
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/templates'))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/static'))

# Initialize Flask app
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Configuration
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'NSjUyKL1$8N*@(i')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['PORT'] = int(os.getenv('PORT', 10000))
CORS(app, origins=["https://your-frontend.onrender.com"], supports_credentials=True)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Error handling
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500

# Routes
@app.route('/')
@app.route('/index')
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

# Run app
if __name__ == '__main__':
    port = int(app.config.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
