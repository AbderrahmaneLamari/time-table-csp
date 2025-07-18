from flask import Flask, jsonify, request, render_template
from time_table_solver import MultiGroupTimeTableCSP, serialize_schedule


app = Flask(__name__)



@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def home():
    return "🎉 Welcome to the CSP Scheduler Flask App!"

@app.route('/api/schedule', methods=['GET'])
def get_schedule():

    csp = MultiGroupTimeTableCSP()
    solution = csp.backtracking_search()

    serialized_solution = serialize_schedule(solution)

    jsoned = jsonify(serialized_solution)
    return jsoned

if __name__ == '__main__':
    app.run(debug=True)
