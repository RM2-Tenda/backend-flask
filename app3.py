from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://u46njtn88k8g4c:pa4077467feb8e12a86a3c9ab0797f7015d81ac8947b38cb3ce2bcee792a1df0a@c2dr1dq7r4d57i.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/dfka5511pjl5t0".replace("://", "ql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    qr_code = db.Column(db.String(255), nullable=True)  # Store QR code data or URL

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(255), nullable=False)

class ButtonState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Boolean, nullable=False, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    if User.query.filter_by(username=username).first():
        return jsonify(message="Username already exists"), 409
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message="User registered successfully"), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify(message="Logged in successfully"), 200
    else:
        return jsonify(message="Invalid username or password"), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify(message="Logged out successfully"), 200

@app.route('/api/button', methods=['GET'])
@login_required
def button():
    button_state = ButtonState.query.first()
    return jsonify(result=button_state.state if button_state else False)

# Additional API endpoints follow similar patterns as above, ensuring @login_required where user-specific actions are needed.

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
