# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import smtplib

app = Flask(__name__)
CORS(app)

# ─────────── Mail Configuration ───────────
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='sachinrao1947@gmail.com',        # ✅ Sender email
    MAIL_PASSWORD='kqzyaemoachcfoex',               # ✅ Your 16-char App Password
    MAIL_DEFAULT_SENDER='sachinrao1947@gmail.com'
)
mail = Mail(app)

# ─────────── Token Serializer ───────────
serializer = URLSafeTimedSerializer('2e3a4fa3-98c9-4d9e-b3e7-e2aa3f781234')

# ─────────── Demo Database ───────────
USERNAME = 'admin'
PASSWORD = 'password123'
USER_EMAILS = {'sachinrao0118@gmail.com': USERNAME}
VERIFIED_EMAILS = set()  # Track activated registrations

# ─────────── Routes ───────────

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    # Only allow login if user is verified
    if data.get('username') == USERNAME and data.get('password') == PASSWORD:
        return jsonify(success=True, message='Login successful')
    return jsonify(success=False, message='Invalid credentials')

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email')
    if email in USER_EMAILS:
        token = serializer.dumps(email, salt='reset-password')
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        msg = Message("Your Password Reset Link", recipients=[email])
        msg.body = (
            "You requested a password reset. Click here to set and confirm your new credentials:\n\n"
            f"{reset_link}\n\nThis link expires in 30 minutes."
        )
        try:
            mail.send(msg)
            print(f"[SUCCESS] Password reset email sent to {email}")
            return jsonify(message='Password reset link sent to your email.')
        except Exception:
            print(f"[DEV] Reset link for {email}: {reset_link}")
            return jsonify(message='Dev mode: reset link printed to console.')
    return jsonify(message='Email not found.'), 404

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    token = serializer.dumps(email, salt='register')
    verify_link = f"http://localhost:3000/register/verify?token={token}"
    msg = Message("Verify Your Registration", recipients=[email])
    msg.body = (
        "Thanks for registering! Click here to verify and activate your account:\n\n"
        f"{verify_link}\n\nThis link expires in 30 minutes."
    )
    try:
        mail.send(msg)
        print(f"[SUCCESS] Registration email sent to {email}")
        return jsonify(message='Verification email sent.')
    except Exception:
        print(f"[DEV] Verify link for {email}: {verify_link}")
        return jsonify(message='Dev mode: verify link printed to console.')

@app.route('/api/register/verify', methods=['POST'])
def verify_registration():
    data = request.get_json() or {}
    token = data.get('token')
    try:
        email = serializer.loads(token, salt='register', max_age=1800)
    except SignatureExpired:
        return jsonify(message='Token expired.'), 400
    except BadSignature:
        return jsonify(message='Invalid token.'), 400
    VERIFIED_EMAILS.add(email)
    return jsonify(message=f'Email {email} has been verified and activated!')

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_user = data.get('newUsername')
    new_pass = data.get('newPassword')
    try:
        email = serializer.loads(token, salt='reset-password', max_age=1800)
    except SignatureExpired:
        return jsonify(message='Token expired.'), 400
    except BadSignature:
        return jsonify(message='Invalid token.'), 400
    global USERNAME, PASSWORD
    USERNAME = new_user
    PASSWORD = new_pass
    print(f"[INFO] Updated credentials for {email}: username = {USERNAME}")
    return jsonify(message='Username & password have been updated.')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
