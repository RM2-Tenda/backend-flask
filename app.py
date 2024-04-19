from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://u46njtn88k8g4c:pa4077467feb8e12a86a3c9ab0797f7015d81ac8947b38cb3ce2bcee792a1df0a@c2dr1dq7r4d57i.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/dfka5511pjl5t0".replace("://", "ql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(255), nullable=False)

class ButtonState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Boolean, nullable=False, default=False)

@app.before_first_request
def create_tables():
    db.create_all()
    if ButtonState.query.first() is None:
        initial_state = ButtonState(state=False)
        db.session.add(initial_state)
        db.session.commit()

@app.route('/api/button', methods=['GET'])
def button():
    button_state = ButtonState.query.first()
    return jsonify(result=button_state.state if button_state else False)

@app.route('/api/button/set', methods=['POST'])
def set_button():
    button_state = ButtonState.query.first()
    new_state = request.json.get('result')
    if new_state is not None:
        if button_state:
            button_state.state = new_state
        else:
            button_state = ButtonState(state=new_state)
            db.session.add(button_state)
        db.session.commit()
        return jsonify(message="Button result set successfully"), 200
    else:
        return jsonify(message="No result provided"), 400

@app.route('/api/statistics', methods=['POST'])
def post_statistics():
    data = request.args.get('data')
    if data:
        new_stat = Statistics(data=data)
        db.session.add(new_stat)
        db.session.commit()
        return jsonify(message="Data added successfully"), 201
    else:
        return jsonify(message="No data provided"), 400

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    stats = Statistics.query.all()
    return jsonify(statistics=[stat.data for stat in stats])

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
