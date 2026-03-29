"""
NoveLang Compilation Pipeline
Orchestrates: NLP Translation → Lexing → Parsing → Semantic Analysis → Interpretation
Returns detailed results from every stage.
"""

import time
import traceback
from nlp_engine import NLPEngine
from lexer import Lexer
from parser_engine import Parser, ParseError
from semantic import SemanticAnalyzer
from interpreter import Interpreter


class Pipeline:
    def __init__(self):
        self.nlp = NLPEngine()
        self.semantic = SemanticAnalyzer()
        self.interpreter = Interpreter()

    def translate_only(self, english_text):
        """Run NLP translation only."""
        start = time.time()
        novelang, analysis = self.nlp.translate(english_text)
        elapsed = round((time.time() - start) * 1000, 2)
        return {
            'success': True,
            'novelang': novelang,
            'nlp_analysis': analysis,
            'time_ms': elapsed,
        }

    def compile_only(self, novelang_code):
        """Run lexer → parser → semantic → interpreter on NoveLang code."""
        stages = []
        overall_start = time.time()

        # ── Stage 1: Lexer ──────────────────────────────────────────────────
        t = time.time()
        try:
            lexer = Lexer(novelang_code)
            tokens = lexer.tokenize()
            token_dicts = [tok.to_dict() for tok in tokens]
            visible_count = len([t for t in tokens if t.type not in ('EOF',)])
            stages.append({
                'name': 'Lexer',
                'status': 'success',
                'time_ms': round((time.time() - t) * 1000, 2),
                'data': token_dicts,
                'summary': f'{visible_count} tokens generated',
            })
        except Exception as e:
            stages.append({
                'name': 'Lexer',
                'status': 'error',
                'time_ms': round((time.time() - t) * 1000, 2),
                'error': str(e),
            })
            return self._result(stages, overall_start, success=False)

        # ── Stage 2: Parser ─────────────────────────────────────────────────
        t = time.time()
        try:
            parser = Parser(tokens)
            ast = parser.parse()
            ast_dict = ast.to_dict()
            stages.append({
                'name': 'Parser',
                'status': 'success',
                'time_ms': round((time.time() - t) * 1000, 2),
                'data': ast_dict,
                'summary': f'AST with {self._count_nodes(ast_dict)} nodes',
            })
        except ParseError as e:
            stages.append({
                'name': 'Parser',
                'status': 'error',
                'time_ms': round((time.time() - t) * 1000, 2),
                'error': str(e),
            })
            return self._result(stages, overall_start, success=False)

        # ── Stage 3: Semantic Analysis ──────────────────────────────────────
        t = time.time()
        try:
            sem_result = self.semantic.analyze(ast)
            stages.append({
                'name': 'Semantic',
                'status': 'success' if sem_result['valid'] else 'warning',
                'time_ms': round((time.time() - t) * 1000, 2),
                'data': sem_result,
                'summary': f"{len(sem_result['symbols'])} symbols, {len(sem_result['errors'])} errors, {len(sem_result['warnings'])} warnings",
            })
            if not sem_result['valid']:
                return self._result(stages, overall_start, success=False)
        except Exception as e:
            stages.append({
                'name': 'Semantic',
                'status': 'error',
                'time_ms': round((time.time() - t) * 1000, 2),
                'error': str(e),
            })
            return self._result(stages, overall_start, success=False)

        # ── Stage 4: Interpreter ────────────────────────────────────────────
        t = time.time()
        try:
            result = self.interpreter.execute(ast)
            stages.append({
                'name': 'Interpreter',
                'status': 'success',
                'time_ms': round((time.time() - t) * 1000, 2),
                'data': result,
                'summary': f"{len(result.get('output', []))} line(s) of output, {len(result.get('trace', []))} steps traced",
            })
        except Exception as e:
            stages.append({
                'name': 'Interpreter',
                'status': 'error',
                'time_ms': round((time.time() - t) * 1000, 2),
                'error': str(e),
            })
            return self._result(stages, overall_start, success=False)

        return self._result(stages, overall_start, success=True)

    def run_all(self, english_text):
        """Full pipeline: English → NoveLang → Compile → Execute."""
        overall_start = time.time()

        # NLP Translation
        nlp_result = self.translate_only(english_text)
        if not nlp_result['success']:
            return {'success': False, 'error': 'NLP translation failed',
                    'nlp': nlp_result, 'compile': None}

        # Compilation + Execution
        compile_result = self.compile_only(nlp_result['novelang'])

        return {
            'success': compile_result['success'],
            'novelang': nlp_result['novelang'],
            'nlp_analysis': nlp_result['nlp_analysis'],
            'nlp_time_ms': nlp_result['time_ms'],
            'stages': compile_result['stages'],
            'total_time_ms': round((time.time() - overall_start) * 1000, 2),
        }

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _result(self, stages, overall_start, success):
        return {
            'success': success,
            'stages': [s for s in stages],
            'total_time_ms': round((time.time() - overall_start) * 1000, 2),
        }

    def _count_nodes(self, d):
        if not isinstance(d, dict):
            return 0
        count = 1
        for child in d.get('children', []):
            count += self._count_nodes(child)
        return count
