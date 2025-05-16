'''from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Hardcoded credentials for demo purposes
USERNAME = 'admin'
PASSWORD = 'password123'

@app.route('/')
def login():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == USERNAME and password == PASSWORD:
        return f"Welcome, {username}!"
    else:
        return render_template('index.html', error="Invalid username or password")

if __name__ == '__main__':
    app.run(debug=True)'''
