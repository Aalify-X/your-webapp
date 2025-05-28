import os
from functools import wraps
from flask import Flask, session, redirect, url_for, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta
from whop import Whop

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
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# CORS Configuration - Only allow Whop domains
WHOP_DOMAINS = [
    'https://whop.com',
    'https://your-whop-subdomain.whop.com',  # Replace with your actual Whop domain
    'https://api.whop.com'
]
CORS(app, origins=WHOP_DOMAINS, supports_credentials=True)

# Whop OAuth Configuration
WHOP_CLIENT_ID = os.getenv('WHOP_CLIENT_ID')
WHOP_CLIENT_SECRET = os.getenv('WHOP_CLIENT_SECRET')
WHOP_REDIRECT_URI = os.getenv('WHOP_REDIRECT_URI', 'https://your-webapp.onrender.com/auth/callback')

# Middleware to verify Whop access
def whop_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip verification for auth callback route
        if request.endpoint == 'auth_callback':
            return f(*args, **kwargs)
            
        # Check for Whop-specific headers or referrer
        whop_referrer = request.headers.get('Referer', '')
        whop_origin = request.headers.get('Origin', '')
        
        # Check if request comes from Whop
        is_whop_request = any(domain in whop_referrer for domain in WHOP_DOMAINS) or \
                         any(domain in whop_origin for domain in WHOP_DOMAINS)
        
        # Check for valid Whop session
        has_whop_session = 'whop_user' in session
        
        if not (is_whop_request or has_whop_session):
            return jsonify({
                "error": "Unauthorized",
                "message": "This application can only be accessed through Whop platform"
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Error handling
@app.errorhandler(403)
def forbidden_error(e):
    return render_template('error.html', 
                         error_code=403,
                         error_message="Access Forbidden - Please use Whop platform to access this application"), 403

@app.errorhandler(404)
def not_found_error(e):
    return render_template('error.html',
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500

# Auth routes
@app.route('/auth/callback')
def auth_callback():
    """Handle Whop OAuth callback"""
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    
    try:
        # Initialize Whop client
        whop = Whop(WHOP_CLIENT_ID, WHOP_CLIENT_SECRET)
        
        # Exchange code for token
        token_data = whop.exchange_code(code)
        access_token = token_data.get('access_token')
        
        if not access_token:
            return redirect(url_for('index'))
            
        # Get user info
        user_info = whop.get_current_user(access_token)
        
        # Store user in session
        session['whop_user'] = {
            'id': user_info.get('id'),
            'email': user_info.get('email'),
            'access_token': access_token
        }
        
        return redirect(url_for('index'))
        
    except Exception as e:
        app.logger.error(f"Auth error: {str(e)}")
        return redirect(url_for('index'))

@app.route('/auth/logout')
def logout():
    """Clear Whop session"""
    session.pop('whop_user', None)
    return redirect(url_for('index'))

# Application routes (all protected with @whop_required)
@app.route('/')
@whop_required
def index():
    return render_template('index.html')

@app.route('/digital_planner')
@whop_required
def digital_planner():
    return render_template('digital_planner.html')

@app.route('/whiteboard')
@whop_required
def whiteboard():
    return render_template('whiteboard.html')

@app.route('/flashcards')
@whop_required
def flashcards():
    return render_template('flashcards.html')

@app.route('/pdf_tools')
@whop_required
def pdf_tools():
    return render_template('pdf_document_intelligence.html')

# API endpoint for token exchange
@app.route('/api/auth/token', methods=['POST'])
def exchange_token():
    """Exchange authorization code for access token"""
    code = request.json.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    try:
        whop = Whop(WHOP_CLIENT_ID, WHOP_CLIENT_SECRET)
        token_data = whop.exchange_code(code)
        return jsonify(token_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Health check endpoint (without Whop requirement)
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

# Run app
if __name__ == '__main__':
    port = int(app.config.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)