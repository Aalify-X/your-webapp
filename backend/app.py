from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))

# Configure logging
app.logger.setLevel(logging.INFO)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = bool(os.getenv('MAIL_USE_TLS', True))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

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
    import nltk
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
    import random
    import string
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pdf_text(pdf_path):
    try:
        import PyPDF2
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

# API Routes
@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    try:
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400
        
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        if pdfminer_available:
            text = extract_text(filepath)
        else:
            text = extract_pdf_text(filepath)
        
        return jsonify({"text": text[:2000]})  # Limit text size
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_flashcards', methods=['POST'])
def generate_flashcards():
    try:
        data = request.get_json()
        text = data.get('text')
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Here, you can implement flashcard generation logic from the text
        # For now, we're just displaying the text
        flashcards = [text]  # Replace with actual flashcard generation logic
        
        return jsonify({"flashcards": flashcards})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_flashcard', methods=['POST'])
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

        # Create unique ID for the flashcard
        new_flashcard = {
            'id': 1,  # Replace with actual ID generation logic
            'front': front,
            'back': back,
            'created_at': "2023-03-08T14:30:00"  # Replace with actual timestamp
        }

        return jsonify({
            'status': 'success',
            'flashcard': new_flashcard
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/api/get_flashcards', methods=['GET'])
def get_flashcards():
    try:
        flashcards = []  # Replace with actual flashcard retrieval logic
        return jsonify({
            'status': 'success',
            'flashcards': flashcards
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

@app.route('/api/delete_flashcard', methods=['POST'])
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
        return jsonify({
            'status': 'success',
            'message': 'Flashcard deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error', 
            'error': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
