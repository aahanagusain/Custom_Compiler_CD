import sys
import os
import unittest

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lexer import Lexer
from parser_engine import Parser
from semantic import SemanticAnalyzer
from interpreter import Interpreter

class TestCompilerPipeline(unittest.TestCase):
    def setUp(self):
        self.lexer = Lexer("")
        self.parser = None
        self.semantic = SemanticAnalyzer()
        self.interpreter = Interpreter()

    def test_lexer_basic(self):
        code = "let x = 10;"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        # Expect 5 tokens: LET, IDENT, EQUALS, NUMBER, SEMI (plus EOF)
        types = [t.type for t in tokens if t.type != 'EOF']
        self.assertEqual(types, ['LET', 'IDENTIFIER', 'EQUALS', 'NUMBER', 'SEMI'])

    def test_parser_with_ids(self):
        code = "let x = 10;"
        tokens = Lexer(code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        ast_dict = ast.to_dict()
        
        # Check if IDs were generated
        self.assertTrue('id' in ast_dict)
        self.assertTrue(ast_dict['id'].startswith('node_'))
        
        # Check child node has ID
        child = ast_dict['children'][0]
        self.assertTrue('id' in child)

    def test_interpreter_trace(self):
        code = """let x = 10;
                  show x + 5;"""
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        
        result = self.interpreter.execute(ast)
        
        # Verify output list
        self.assertIn('15', result['output'])
        
        # Verify trace existed
        trace = result['trace']
        self.assertTrue(len(trace) > 0)
        
        # Find step where x is assigned or shown
        has_x_in_vars = False
        for step in trace:
            if 'x' in step['variables']:
                has_x_in_vars = True
                self.assertEqual(step['variables']['x'], 10)
        self.assertTrue(has_x_in_vars, "Variable 'x' should appear in execution trace")

    def test_semantic_analysis(self):
        code = "let a = 5; show a;"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        sem = self.semantic.analyze(ast)
        self.assertTrue(sem['valid'])
        self.assertEqual(len(sem['errors']), 0)

    def test_error_handling(self):
        # Undeclared variable
        code = "show y;"
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        result = self.interpreter.execute(ast)
        # Interpreter catch RuntimeError
        self.assertTrue(any("Runtime Error" in line for line in result['output']))

if __name__ == '__main__':
    unittest.main()
