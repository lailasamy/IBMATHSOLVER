from sympy import symbols, expand, simplify, factor, sympify
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        expression = data['expression'].replace('^', '**')  # Replace ^ with ** for power
        operation = data['operation']
        expr = sympify(expression)  # Convert string expression to SymPy expression

        if operation == 'expand':
            result = expand(expr)
        elif operation == 'simplify':
            result = simplify(expr)
        elif operation == 'factor':
            result = factor(expr)
        else:
            result = expr

        return jsonify({
            'original': str(expr),
            'result': str(result),
            'operation': operation
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
