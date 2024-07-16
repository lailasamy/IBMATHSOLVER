from sympy import symbols, expand, simplify, factor, sympify, binomial, solve, I, pi, exp, log, cos, sin, tan, acos, asin, atan, degree, Poly
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

def extract_symbols(expression):
    # Extract variable names from the expression
    return set(re.findall(r'[a-zA-Z]\w*', expression))

def insert_multiplication_operators(expression):
    # Insert explicit multiplication operators
    expression = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expression)
    expression = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', expression)
    expression = re.sub(r'([a-zA-Z])([a-zA-Z])', r'\1*\2', expression)
    return expression

def factor_steps(expr):
    steps = []
    poly_expr = Poly(expr)
    if degree(poly_expr) == 2:
        a, b, c = poly_expr.all_coeffs()
        steps.append(f"The middle number is {b} and the last number is {c}.")
        steps.append("Factoring means we want something like (x+_)(x+_)")
        steps.append("Which numbers go in the blanks?")
        steps.append(f"We need two numbers that add together to get {b} and multiply together to get {c}.")
        
        for i in range(1, abs(c) + 1):
            if c % i == 0:
                j = c // i
                if i + j == b:
                    steps.append(f"Try {i} and {j}: {i}+{j} = {b} and {i}*{j} = {c}")
                    steps.append(f"Fill in the blanks in (x+_)(x+_) with {i} and {j} to get (x+{i})(x+{j})")
                    break
                elif -i + -j == b:
                    steps.append(f"Try {-i} and {-j}: {-i}+{-j} = {b} and {-i}*{-j} = {c}")
                    steps.append(f"Fill in the blanks in (x+_)(x+_) with {-i} and {-j} to get (x{-i})(x{-j})")
                    break

    factored_expr = factor(expr)
    steps.append(f"Answer: {factored_expr}")
    return steps, factored_expr

def handle_composite_functions(f_expr, g_expr):
    x = symbols('x')
    f = sympify(f_expr)
    g = sympify(g_expr)
    composite_expr = f.subs(x, g)
    steps = [
        f"Expression for f: {f_expr}",
        f"Expression for g: {g_expr}",
        f"Composite function: f(g(x)) = {f_expr}.subs(x, {g_expr}) = {composite_expr}"
    ]
    return steps, composite_expr

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        if not data or 'expression' not in data:
            return jsonify({'error': 'Invalid input data'}), 400
        
        expression = data['expression'].replace('^', '**')  # Replace ^ with ** for power
        expression = insert_multiplication_operators(expression)  # Handle implicit multiplication
        
        # Extract and define symbols
        symbol_names = extract_symbols(expression)
        symbols_dict = {name: symbols(name) for name in symbol_names}
        
        # Attempt to parse the expression
        try:
            expr = sympify(expression, locals=symbols_dict)  # Convert string expression to SymPy expression
        except Exception as e:
            return jsonify({'error': f'Error parsing expression: {e}'}), 400

        steps = []
        result = None

        # Automatically determine the appropriate operation based on the expression
        if expr.is_polynomial():
            if degree(expr) == 2:
                steps, result = factor_steps(expr)
            else:
                result = factor(expr)
                steps.append(f"Factored expression: {result}")
        elif expr.is_Add or expr.is_Mul or expr.is_Pow:
            result = simplify(expr)
            steps.append(f"Simplified expression: {result}")
        elif 'binomial' in expression:
            n, k = symbols('n k')
            result = binomial(n, k).expand(func=True)
            steps.append(f"Binomial expansion: {result}")
        elif any(sym in expression for sym in ['log', 'exp']):
            if 'log' in expression:
                result = log(expr)
                steps.append(f"Logarithm of the expression: {result}")
            else:
                result = exp(expr)
                steps.append(f"Exponential of the expression: {result}")
        elif expr.has(I):
            result = expr.as_real_imag()
            steps.append(f"Complex number as real and imaginary parts: {result}")
        elif isinstance(expr, (int, float)):
            result = expr
            steps.append(f"Evaluated result: {result}")
        else:
            result = expr.evalf()  # Evaluate the expression numerically
            steps.append(f"Evaluated result: {result}")

        return jsonify({
            'original': str(expr),
            'result': str(result),
            'steps': steps
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/composite_functions', methods=['POST'])
def composite_functions():
    try:
        data = request.json
        if not data or 'f_expr' not in data or 'g_expr' not in data:
            return jsonify({'error': 'Invalid input data'}), 400
        
        f_expr = data['f_expr'].replace('^', '**')
        g_expr = data['g_expr'].replace('^', '**')
        
        # Handle implicit multiplication
        f_expr = insert_multiplication_operators(f_expr)
        g_expr = insert_multiplication_operators(g_expr)
        
        # Extract and define symbols
        symbol_names_f = extract_symbols(f_expr)
        symbol_names_g = extract_symbols(g_expr)
        symbol_names = symbol_names_f.union(symbol_names_g)
        symbols_dict = {name: symbols(name) for name in symbol_names}
        
        # Attempt to parse the expressions
        try:
            f = sympify(f_expr, locals=symbols_dict)
            g = sympify(g_expr, locals=symbols_dict)
        except Exception as e:
            return jsonify({'error': f'Error parsing expression: {e}'}), 400

        steps, result = handle_composite_functions(f, g)

        return jsonify({
            'f_expr': str(f),
            'g_expr': str(g),
            'result': str(result),
            'steps': steps
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
