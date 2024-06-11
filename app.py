from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://u46njtn88k8g4c:pa4077467feb8e12a86a3c9ab0797f7015d81ac8947b38cb3ce2bcee792a1df0a@c2dr1dq7r4d57i.cluster-czz5s0kz4scl.eu-west-1.rds.amazonaws.com:5432/dfka5511pjl5t0".replace(
    "://", "ql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    presence = db.Column(db.Boolean, nullable=False)
    gas_value = db.Column(db.Integer, nullable=False)
    gas_detected = db.Column(db.Boolean, nullable=False)
    uv_value = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())


class ButtonState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Boolean, nullable=False, default=False)


class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(255), nullable=False)
    device_id = db.Column(db.String(50), nullable=False)


class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    comparison = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    days = db.Column(db.String(50), nullable=True)
    start_time = db.Column(db.String(5), nullable=True)
    end_time = db.Column(db.String(5), nullable=True)
    device_id = db.Column(db.String(50), nullable=False)


def create_tables():
    db.create_all()
    # Ensure a default button state exists
    if ButtonState.query.first() is None:
        initial_state = ButtonState(state=False)
        db.session.add(initial_state)
        db.session.commit()


with app.app_context():
    create_tables()  # This will execute at application start


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
    data = request.json
    if data:
        new_stat = Statistics(
            device_id=data.get('device_id'),
            humidity=data.get('humidity'),
            temperature=data.get('temperature'),
            presence=bool(data.get('presence')),
            gas_value=data.get('gas_value'),
            gas_detected=bool(data.get('gas_detected')),
            uv_value=data.get('uv_value'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        db.session.add(new_stat)
        db.session.commit()
        return jsonify(message="Data added successfully"), 201
    else:
        return jsonify(message="No data provided"), 400


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    device_id = request.args.get('device_id')
    if device_id:
        latest_stat = Statistics.query.filter_by(device_id=device_id).order_by(Statistics.id.desc()).first()
        if latest_stat:
            return jsonify(
                humidity=latest_stat.humidity,
                temperature=latest_stat.temperature,
                presence=latest_stat.presence,
                gas_value=latest_stat.gas_value,
                gas_detected=latest_stat.gas_detected,
                uv_value=latest_stat.uv_value,
                latitude=latest_stat.latitude,
                longitude=latest_stat.longitude
            )
        else:
            return jsonify(message="No data found for the given device_id"), 404
    else:
        return jsonify(message="No device_id provided"), 400


@app.route('/api/statistics/history', methods=['GET'])
def get_statistics_history():
    device_id = request.args.get('device_id')
    if device_id:
        stats = Statistics.query.filter_by(device_id=device_id).order_by(Statistics.timestamp.desc()).all()
        return jsonify(statistics=[{
            'timestamp': stat.timestamp,
            'humidity': stat.humidity,
            'temperature': stat.temperature,
            'presence': stat.presence,
            'gas_value': stat.gas_value,
            'gas_detected': stat.gas_detected,
            'uv_value': stat.uv_value,
            'latitude': stat.latitude,
            'longitude': stat.longitude
        } for stat in stats])
    else:
        return jsonify(message="No device_id provided"), 400


@app.route('/api/commands', methods=['POST'])
def post_command():
    command = request.json.get('command')
    device_id = request.json.get('device_id')
    if command and device_id:
        new_command = Command(command=command, device_id=device_id)
        db.session.add(new_command)
        db.session.commit()
        return jsonify(message="Command added successfully"), 201
    else:
        return jsonify(message="No command or device_id provided"), 400


@app.route('/api/commands', methods=['GET'])
def get_commands():
    device_id = request.args.get('device_id')
    if device_id:
        commands = Command.query.filter_by(device_id=device_id).all()
        if commands:
            latest_command = commands[-1].command
            return jsonify(command=latest_command)
        else:
            return jsonify(command="")
    else:
        return jsonify(message="No device_id provided"), 400


@app.route('/api/commands/clear', methods=['POST'])
def clear_commands():
    device_id = request.json.get('device_id')
    if device_id:
        Command.query.filter_by(device_id=device_id).delete()
        db.session.commit()
        return jsonify(message="Commands cleared successfully"), 200
    else:
        return jsonify(message="No device_id provided"), 400


@app.route('/api/alarms', methods=['POST'])
def post_alarm():
    data = request.json
    if data:
        new_alarm = Alarm(
            sensor=data.get('sensor'),
            condition=data.get('condition'),
            comparison=data.get('comparison'),
            value=data.get('value'),
            days=data.get('days'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            device_id=data.get('device_id')
        )
        db.session.add(new_alarm)
        db.session.commit()
        return jsonify(message="Alarm added successfully"), 201
    else:
        return jsonify(message="No data provided"), 400


@app.route('/api/alarms', methods=['GET'])
def get_alarms():
    device_id = request.args.get('device_id')
    if device_id:
        alarms = Alarm.query.filter_by(device_id=device_id).all()
        return jsonify(alarms=[{
            'id': alarm.id,
            'sensor': alarm.sensor,
            'condition': alarm.condition,
            'comparison': alarm.comparison,
            'value': alarm.value,
            'days': alarm.days,
            'start_time': alarm.start_time,
            'end_time': alarm.end_time
        } for alarm in alarms])
    else:
        return jsonify(message="No device_id provided"), 400

@app.route('/api/alarms/clear', methods=['POST'])
def clear_alarms():
    device_id = request.json.get('device_id')
    if device_id:
        Alarm.query.filter_by(device_id=device_id).delete()
        db.session.commit()
        return jsonify(message="Alarms cleared successfully"), 200
    else:
        return jsonify(message="No device_id provided"), 400

@app.route('/api/alarms/<int:alarm_id>', methods=['DELETE'])
def delete_alarm(alarm_id):
    alarm = Alarm.query.get(alarm_id)
    if alarm:
        db.session.delete(alarm)
        db.session.commit()
        return jsonify(message="Alarm deleted successfully"), 200
    else:
        return jsonify(message="Alarm not found"), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)