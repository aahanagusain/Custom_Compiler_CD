import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from nlp_engine import NLPEngine
from lexer import Lexer
from parser_engine import Parser, ParseError

code = """define a function called factorial that takes n
  create a variable called result and set it to 1
  create a variable called counter and set it to 1
  repeat while counter is less than or equal to n
    set result to result times counter
    increment counter
  end
  give result
end
print "Factorial of 5:"
create a variable called answer and set it to 0
let answer = factorial(5);
print answer"""

nlp = NLPEngine()
script, _ = nlp.translate(code)
print("--- NOVELANG SCRIPT ---")
print(script)
print("-----------------------")

lex = Lexer(script)
tokens = lex.tokenize()

try:
    p = Parser(tokens)
    ast = p.parse()
    print("PARSING SUCCESS")
except ParseError as e:
    print(f"PARSING ERROR: {e}")
