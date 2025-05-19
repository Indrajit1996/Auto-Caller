from flask import Blueprint, request, jsonify
from app import mail, serializer
from flask_mail import Message
from itsdangerous import BadSignature, SignatureExpired

auth_blueprint = Blueprint('auth', __name__)

# In-memory store
USERNAME = 'sachinrao0118@gmail.com'
PASSWORD = 'password123'
USER_EMAILS = {'sachinrao0118@gmail.com': USERNAME}
VERIFIED_EMAILS = set()

@auth_blueprint.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    if data.get('username') == USERNAME and data.get('password') == PASSWORD:
        return jsonify(success=True, message='Login successful')
    return jsonify(success=False, message='Invalid credentials')

@auth_blueprint.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email')
    if email in USER_EMAILS:
        token = serializer.dumps(email, salt='reset-password')
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        msg = Message("Your Password Reset Link", recipients=[email])
        msg.body = f"Reset link:\n{reset_link}\n\nThis link expires in 30 minutes."
        try:
            mail.send(msg)
            return jsonify(message='Password reset link sent.')
        except Exception:
            print(f"[DEV] Reset link: {reset_link}")
            return jsonify(message='Dev mode: link printed.')
    return jsonify(message='Email not found.'), 404

@auth_blueprint.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    token = serializer.dumps(email, salt='register')
    verify_link = f"http://localhost:3000/register/verify?token={token}"
    msg = Message("Verify Registration", recipients=[email])
    msg.body = f"Verify link:\n{verify_link}\n\nExpires in 30 minutes."
    try:
        mail.send(msg)
        return jsonify(message='Verification email sent.')
    except Exception:
        print(f"[DEV] Verify link: {verify_link}")
        return jsonify(message='Dev mode: link printed.')

@auth_blueprint.route('/api/register/verify', methods=['POST'])
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
    return jsonify(message=f'Email {email} verified!')

@auth_blueprint.route('/api/reset-password', methods=['POST'])
def reset_password():
    global USERNAME, PASSWORD
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
    USERNAME = new_user
    PASSWORD = new_pass
    return jsonify(message='Username & password updated.')
