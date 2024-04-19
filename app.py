from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

statistics_data = []

button_result = None

@app.route('/api/button', methods=['GET'])
def button():
    if button_result is not None:
        return jsonify(result=button_result)
    else:
        return jsonify(result=False)

@app.route('/api/button/set', methods=['POST'])
def set_button():
    global button_result
    data = request.json.get('result')
    if data is not None:
        button_result = data
        return jsonify(message="Button result set successfully"), 200
    else:
        return jsonify(message="No result provided"), 400

@app.route('/api/statistics', methods=['POST'])
def post_statistics():
    data = request.args.get('data')
    if data:
        statistics_data.append(data)
        return jsonify(message="Data added successfully"), 201
    else:
        return jsonify(message="No data provided"), 400

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    return jsonify(statistics=statistics_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
