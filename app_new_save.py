from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://u46njtn88k8g4c:pa4077467feb8e12a86a3c9ab0797f7015d81ac8947b38cb3ce2bcee792a1df0a@c2dr1dq7r4d57i.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/dfka5511pjl5t0".replace("://", "ql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'jwt_secret'  # Change this to a real secret key
jwt = JWTManager(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    qr_codes = db.relationship('QRCode', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_status = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/api/devices/register', methods=['POST'])
def register_device():
    device_id = request.json.get('device_id')
    if device_id:
        qr_code = QRCode.query.filter_by(code=device_id).first()
        if qr_code:
            qr_code.device_status = True
            db.session.commit()
            return jsonify(message="Device registered and online"), 200
        else:
            return jsonify(message="QR Code does not exist"), 404
    return jsonify(message="No Device ID provided"), 400

@app.route('/api/qr', methods=['POST'])
@jwt_required() 
def add_qr_code():
    qr_code_data = request.json.get('qr_code')
    if qr_code_data:
        existing_device = QRCode.query.filter_by(code=qr_code_data).first()
        if existing_device:
            return jsonify(message="Device already registered"), 409
        new_qr_code = QRCode(code=qr_code_data, user_id=current_user.id)
        db.session.add(new_qr_code)
        db.session.commit()
        return jsonify(message="QR Code added successfully, awaiting device registration"), 200
    return jsonify(message="No QR Code provided"), 400

@app.route('/api/qr/<int:qr_id>', methods=['DELETE'])
@jwt_required() 
def delete_qr_code(qr_id):
    qr_code = QRCode.query.filter_by(id=qr_id, user_id=current_user.id).first()
    if qr_code:
        db.session.delete(qr_code)
        db.session.commit()
        return jsonify(message="QR Code deleted successfully"), 200
    return jsonify(message="QR Code not found"), 404

@app.route('/api/qr', methods=['GET'])
@jwt_required() 
def get_qr_codes():
    qr_codes = QRCode.query.filter_by(user_id=current_user.id).all()
    return jsonify(qr_codes=[{'code': qr.code, 'status': qr.device_status} for qr in qr_codes]), 200

class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(255), nullable=False)
    data = db.Column(db.String(255), nullable=False)

@app.route('/api/statistics', methods=['POST'])
def post_statistics():
    device_id = request.json.get('device_id')
    data = request.json.get('data')
    if device_id and data:
        new_stat = Statistics(device_id=device_id, data=data)
        db.session.add(new_stat)
        db.session.commit()
        return jsonify(message="Data added successfully"), 201
    else:
        return jsonify(message="Missing device ID or data"), 400

class ButtonState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Boolean, nullable=False, default=False)


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    stats = Statistics.query.all()
    return jsonify(statistics=[stat.data for stat in stats])

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
        access_token = create_access_token(identity=username)
        return jsonify(message="Logged in successfully", token=access_token), 200
    else:
        return jsonify(message="Invalid username or password"), 401

@app.route('/logout')
@jwt_required() 
def logout():
    logout_user()
    return jsonify(message="Logged out successfully"), 200

@app.route('/api/button', methods=['GET'])
@jwt_required() 
def button():
    button_state = ButtonState.query.first()
    return jsonify(result=button_state.state if button_state else False)

# @app.route('/reset-database')
# def reset_database():
#     db.drop_all()
#     return jsonify(message="All tables dropped"), 200

# @app.route('/create-database')
# def create_database():
#     db.create_all()
#     return jsonify(message="All tables created"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
