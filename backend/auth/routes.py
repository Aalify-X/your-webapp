from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, auth
import random
import smtplib
from email.message import EmailMessage
import os

auth_bp = Blueprint('auth', __name__, template_folder='../../frontend/templates')

# Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

# Route to show login page
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))  # already logged in

    if request.method == 'POST':
        # Simple email field used for login
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash("Please enter your email.")
            return redirect(url_for('auth.login'))

        session.permanent = True
        session['user'] = email  # Set user session
        return redirect(url_for('index'))

    return render_template('login.html')

# Route to send OTP
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    print("OTP route called")

    email = request.form.get('email', '').strip().lower()
    print("Email received:", email)

    if not email:
        flash("Please enter your email.")
        return redirect(url_for('auth.login'))

    otp = str(random.randint(100000, 999999))  # Generate 6-digit OTP

    subject = "Your OTP for Aalifyx Login"
    body = f"Your OTP is: {otp}\nDo not share it with anyone."

    try:
        send_email(email, subject, body)
        session['email'] = email
        session['otp'] = otp
        print("OTP email sent successfully")
        return redirect(url_for('auth.verify_otp'))
    except Exception as e:
        print("Failed to send OTP:", e)
        flash("Failed to send OTP. Try again.")
        return redirect(url_for('auth.login'))

# Route to verify OTP
@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_input_otp = request.form.get('otp')
        actual_otp = session.get('otp')
        email = session.get('email')

        if not actual_otp or not email:
            flash("Session expired. Please try again.")
            return redirect(url_for('auth.login'))

        if user_input_otp == actual_otp:
            session.pop('otp', None)
            session.pop('email', None)
            session['user'] = email  # Important: Define this correctly
            session.permanent = True

            return redirect(url_for('index'))  # Check this next
        else:
            flash("Invalid OTP. Please try again.")
            return redirect(url_for('auth.verify_otp'))

    return render_template('verify_otp.html')



# Logout Route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# Email sending function
def send_email(to_email, subject, body):
    EMAIL_ADDRESS = 'dev.aalifyx@gmail.com'
    EMAIL_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')  # Should be set in environment variables

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
