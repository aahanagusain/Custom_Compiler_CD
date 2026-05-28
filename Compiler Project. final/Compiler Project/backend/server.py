"""
NoveLang Server — Flask API serving the NLP Compiler and frontend.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pipeline import Pipeline

# ── App Setup ───────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

pipeline = Pipeline()

# ── Example Programs ────────────────────────────────────────────────────────────

EXAMPLES = {
    'hello_world': {
        'name': 'Hello World',
        'description': 'A simple program that prints a greeting',
        'english': 'create a variable called greeting and set it to "Hello, World!"\nprint greeting\nprint "Welcome to NoveLang!"',
    },
    'calculator': {
        'name': 'Simple Calculator',
        'description': 'Perform basic arithmetic operations',
        'english': 'create a variable called a and set it to 15\ncreate a variable called b and set it to 7\nprint "Addition:"\nprint a plus b\nprint "Subtraction:"\nprint a minus b\nprint "Multiplication:"\nprint a times b\nprint "Division:"\nprint a divided by b',
    },
    'conditionals': {
        'name': 'Age Checker',
        'description': 'Use if-else to check conditions',
        'english': 'create a variable called age and set it to 20\nif age is greater than or equal to 18 then\n  print "You are an adult!"\n  print "You can vote."\notherwise\n  print "You are a minor."\n  print "Come back later!"\nend\nprint "Program complete."',
    },
    'loop_example': {
        'name': 'Number Printer',
        'description': 'Loop through numbers and print them',
        'english': 'print "Counting from 1 to 5:"\nloop from 1 to 5\n  print i\nend\nprint "Done counting!"',
    },
    'factorial': {
        'name': 'Factorial Calculator',
        'description': 'Calculate factorial using a function',
        'english': 'define a function called factorial that takes n\n  create a variable called result and set it to 1\n  create a variable called counter and set it to 1\n  repeat while counter is less than or equal to n\n    set result to result times counter\n    increment counter\n  end\n  give result\nend\nprint "Factorial of 5:"\ncreate a variable called answer and set it to 0\nlet answer = factorial(5);\nprint answer',
    },
    'fibonacci': {
        'name': 'Fibonacci Sequence',
        'description': 'Generate Fibonacci numbers',
        'english': 'create a variable called a and set it to 0\ncreate a variable called b and set it to 1\nprint "Fibonacci Sequence:"\nprint a\nprint b\nloop from 1 to 8\n  create a variable called temp and set it to a plus b\n  set a to b\n  set b to temp\n  print temp\nend',
    },
    'fizzbuzz': {
        'name': 'FizzBuzz',
        'description': 'Classic FizzBuzz programming challenge',
        'english': 'print "FizzBuzz from 1 to 15:"\nloop from 1 to 15\n  create a variable called mod3 and set it to i modulo 3\n  create a variable called mod5 and set it to i modulo 5\n  if mod3 == 0 and mod5 == 0 then\n    print "FizzBuzz"\n  end\n  if mod3 == 0 and mod5 != 0 then\n    print "Fizz"\n  end\n  if mod3 != 0 and mod5 == 0 then\n    print "Buzz"\n  end\n  if mod3 != 0 and mod5 != 0 then\n    print i\n  end\nend',
    },
    'geometry_calculator': {
        'name': 'Geometry Calculator',
        'description': 'Calculates shapes properties (includes redundant logic optimized away)',
        'english': 'create a variable called radius and set it to 10\ncreate a variable called pi and set it to 3\ncreate a variable called diameter and set it to radius times 2\ncreate a variable called circumference and set it to pi times diameter\ncreate a variable called unused_area and set it to pi times radius times radius\nprint "Circumference:"\nprint circumference\nif false then\n  print "This branch is dead code"\nend',
    },
    'physics_engine': {
        'name': 'Physics Simulator',
        'description': 'Simulates simple physics (shows constant folding & strength reduction)',
        'english': 'create a variable called mass and set it to 25\ncreate a variable called acceleration and set it to 10\ncreate a variable called force and set it to mass times acceleration\ncreate a variable called static_friction and set it to 0\ncreate a variable called net_force and set it to force minus static_friction\ncreate a variable called doubled_force and set it to net_force times 2\nprint "Net Force:"\nprint net_force\nprint "Doubled Force:"\nprint doubled_force\nif 1 == 2 then\n  print "Impossible physics state"\nend',
    },
    'temperature_converter': {
        'name': 'Temperature Converter',
        'description': 'Converts Celsius to Fahrenheit with redundant algebra',
        'english': 'create a variable called celsius and set it to 30\ncreate a variable called base and set it to 32\ncreate a variable called unused_temp and set it to 100\ncreate a variable called multiplier and set it to 9\ncreate a variable called fahrenheit and set it to celsius times multiplier divided by 5 plus base plus 0\nprint "Fahrenheit:"\nprint fahrenheit',
    },
    'banking_system': {
        'name': 'Banking System',
        'description': 'Calculates bank balance with hidden dead code',
        'english': 'create a variable called balance and set it to 1000\ncreate a variable called deposit and set it to 500\ncreate a variable called fee and set it to 0\ncreate a variable called new_balance and set it to balance plus deposit minus fee\nprint "New Balance:"\nprint new_balance\nif 0 > 1 then\n  print "Account overdrawn!"\nend',
    },
    'math_operations': {
        'name': 'Math Operations',
        'description': 'Showcases strength reduction and algebraic simplification',
        'english': 'create a variable called x and set it to 42\ncreate a variable called doubled and set it to x times 2\ncreate a variable called identity and set it to x times 1\ncreate a variable called zeroed and set it to x times 0\nprint "Doubled:"\nprint doubled\nprint "Identity:"\nprint identity',
    },
}

# ── Routes ──────────────────────────────────────────────────────────────────────

@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    # Don't intercept API routes
    if path.startswith('api/'):
        from flask import abort
        abort(404)
    return send_from_directory(FRONTEND_DIR, path)



@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.get_json(force=True)
    english = data.get('english', '')
    if not english.strip():
        return jsonify({'success': False, 'error': 'No English text provided'}), 400
    try:
        result = pipeline.translate_only(english)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compile', methods=['POST'])
def compile_code():
    data = request.get_json(force=True)
    code = data.get('code', '')
    if not code.strip():
        return jsonify({'success': False, 'error': 'No NoveLang code provided'}), 400
    try:
        result = pipeline.compile_only(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/optimize', methods=['POST'])
def optimize_code():
    data = request.get_json(force=True)
    code = data.get('code', '')
    if not code.strip():
        return jsonify({'success': False, 'error': 'No NoveLang code provided'}), 400
    try:
        result = pipeline.optimize_only(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/run-all', methods=['POST'])
def run_all():
    data = request.get_json(force=True)
    english = data.get('english', '')
    if not english.strip():
        return jsonify({'success': False, 'error': 'No English text provided'}), 400
    try:
        result = pipeline.run_all(english)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/examples', methods=['GET'])
def get_examples():
    listing = []
    for key, ex in EXAMPLES.items():
        listing.append({
            'id': key,
            'name': ex['name'],
            'description': ex['description'],
        })
    return jsonify(listing)


@app.route('/api/examples/<example_id>', methods=['GET'])
def get_example(example_id):
    ex = EXAMPLES.get(example_id)
    if not ex:
        return jsonify({'success': False, 'error': 'Example not found'}), 404
    return jsonify({'success': True, **ex})


# ── Main ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("   🧠  NoveLang AI Compiler Server")
    print("   🌐  http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
