from flask import Flask, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from db import get_engine

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

engine = get_engine()

# Registration endpoint (includes duplicate username check + email + nickname)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    nickname = data.get('nickname')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    with engine.connect() as conn:
        # Check if the username already exists
        result = conn.execute(
            text("SELECT id FROM users WHERE username = :u"),
            {'u': username}
        ).fetchone()

        if result:
            return jsonify({'error': 'Username already exists'}), 409

        # Insert new user
        conn.execute(
            text("""
                INSERT INTO users (username, password, email, nickname)
                VALUES (:u, :p, :e, :n)
            """),
            {
                'u': username,
                'p': generate_password_hash(password),
                'e': email,
                'n': nickname
            }
        )
    return jsonify({'message': 'Registration successful!'})

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM users WHERE username = :u"),
            {'u': username}
        ).fetchone()

    if user and check_password_hash(user['password'], password):
        session['username'] = username
        return jsonify({'message': 'Login successful!'})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

# Profile endpoint (requires login)
@app.route('/profile')
def profile():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in'}), 403

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT username, email, nickname, created_at FROM users WHERE username = :u"),
            {'u': session['username']}
        ).fetchone()

    return jsonify({
        'username': user['username'],
        'email': user['email'],
        'nickname': user['nickname'],
        'created_at': user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    })

# Password change endpoint (requires login)
@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in'}), 403

    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({'error': 'Both old and new passwords are required'}), 400

    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT password FROM users WHERE username = :u"),
            {'u': session['username']}
        ).fetchone()

        if not user or not check_password_hash(user['password'], old_password):
            return jsonify({'error': 'Old password is incorrect'}), 403

        conn.execute(
            text("UPDATE users SET password = :p WHERE username = :u"),
            {
                'p': generate_password_hash(new_password),
                'u': session['username']
            }
        )
    return jsonify({'message': 'Password changed successfully'})

# Logout endpoint
@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'})

if __name__ == '__main__':
    app.run(debug=True)