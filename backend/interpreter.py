"""
NoveLang Interpreter — AST-walking interpreter.
Executes the AST produced by the parser, managing environments and capturing output.
"""

from parser_engine import (
    Program, LetStmt, AssignStmt, ShowStmt, CheckStmt,
    RepeatRangeStmt, RepeatWhileStmt, TaskStmt, GiveStmt, InputStmt,
    BinaryExpr, UnaryExpr, CallExpr, Identifier, NumberLit, StringLit, BoolLit,
)


class ReturnSignal(Exception):
    """Used to unwind the call stack when a 'give' statement is hit."""
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.store = {}
        self.parent = parent

    def get(self, name):
        if name in self.store:
            return self.store[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def set(self, name, value):
        self.store[name] = value

    def assign(self, name, value):
        if name in self.store:
            self.store[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise RuntimeError(f"Cannot assign to undeclared variable '{name}'")


class NoveLangFunction:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


class Interpreter:
    MAX_ITERATIONS = 10000

    def __init__(self):
        self.output = []
        self.env = Environment()
        self.input_values = []
        self.input_index = 0

    def set_inputs(self, inputs):
        self.input_values = inputs
        self.input_index = 0

    def execute(self, ast):
        self.output = []
        self.env = Environment()
        self.input_index = 0
        try:
            self._exec(ast)
        except ReturnSignal:
            pass
        except RuntimeError as e:
            self.output.append(f"[Runtime Error] {e}")
        except Exception as e:
            self.output.append(f"[Error] {e}")
        return {
            'output': self.output
        }

    def _exec(self, node):
        
        method = f'_exec_{type(node).__name__}'
        executor = getattr(self, method, None)
        if executor:
            return executor(node)
        raise RuntimeError(f"Unknown AST node: {type(node).__name__}")

    def _eval(self, node):

        method = f'_eval_{type(node).__name__}'
        evaluator = getattr(self, method, None)
        if evaluator:
            return evaluator(node)
        # If it's a statement-like node used as expression (bare expression stmts)
        exec_method = f'_exec_{type(node).__name__}'
        executor = getattr(self, exec_method, None)
        if executor:
            return executor(node)
        raise RuntimeError(f"Cannot evaluate node: {type(node).__name__}")

    # ── Statements ──────────────────────────────────────────────────────────

    def _exec_Program(self, node):
        for stmt in node.stmts:
            self._exec(stmt)

    def _exec_LetStmt(self, node):
        value = self._eval(node.value)
        self.env.set(node.name, value)

    def _exec_AssignStmt(self, node):
        value = self._eval(node.value)
        try:
            self.env.assign(node.name, value)
        except RuntimeError:
            self.env.set(node.name, value)

    def _exec_ShowStmt(self, node):
        value = self._eval(node.value)
        self.output.append(str(value))

    def _exec_CheckStmt(self, node):
        cond = self._eval(node.cond)
        child_env = Environment(self.env)
        old = self.env
        self.env = child_env
        if self._truthy(cond):
            for s in node.body:
                self._exec(s)
        elif node.else_body:
            for s in node.else_body:
                self._exec(s)
        self.env = old

    def _exec_RepeatRangeStmt(self, node):
        start = int(self._eval(node.start))
        end = int(self._eval(node.end))
        child_env = Environment(self.env)
        old = self.env
        self.env = child_env
        iterations = 0
        for i in range(start, end + 1):
            iterations += 1
            if iterations > self.MAX_ITERATIONS:
                self.output.append("[Runtime Error] Maximum loop iterations exceeded")
                break
            self.env.set(node.var, i)
            for s in node.body:
                self._exec(s)
        self.env = old

    def _exec_RepeatWhileStmt(self, node):
        child_env = Environment(self.env)
        old = self.env
        self.env = child_env
        iterations = 0
        while self._truthy(self._eval(node.cond)):
            iterations += 1
            if iterations > self.MAX_ITERATIONS:
                self.output.append("[Runtime Error] Maximum loop iterations exceeded")
                break
            for s in node.body:
                self._exec(s)
        self.env = old

    def _exec_TaskStmt(self, node):
        func = NoveLangFunction(node.name, node.params, node.body, self.env)
        self.env.set(node.name, func)

    def _exec_GiveStmt(self, node):
        value = self._eval(node.value)
        raise ReturnSignal(value)

    def _exec_InputStmt(self, node):
        if self.input_index < len(self.input_values):
            val = self.input_values[self.input_index]
            self.input_index += 1
        else:
            val = "user_input"
        try:
            val = int(val)
        except (ValueError, TypeError):
            try:
                val = float(val)
            except (ValueError, TypeError):
                pass
        self.env.set(node.name, val)
        self.output.append(f"[Input] {node.name} = {val}")

    # ── Expressions ─────────────────────────────────────────────────────────

    def _eval_NumberLit(self, node):
        return node.value

    def _eval_StringLit(self, node):
        return node.value

    def _eval_BoolLit(self, node):
        return node.value

    def _eval_Identifier(self, node):
        return self.env.get(node.name)

    def _eval_BinaryExpr(self, node):
        left = self._eval(node.left)
        right = self._eval(node.right)
        op = node.op
        try:
            if op == '+':
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            if op == '-':
                return left - right
            if op == '*':
                return left * right
            if op == '/':
                if right == 0:
                    raise RuntimeError("Division by zero")
                return left / right
            if op == '%':
                if right == 0:
                    raise RuntimeError("Modulo by zero")
                return left % right
            if op == '>':
                return left > right
            if op == '<':
                return left < right
            if op == '>=':
                return left >= right
            if op == '<=':
                return left <= right
            if op == '==':
                return left == right
            if op == '!=':
                return left != right
            if op == 'and':
                return self._truthy(left) and self._truthy(right)
            if op == 'or':
                return self._truthy(left) or self._truthy(right)
        except TypeError as e:
            raise RuntimeError(f"Type error in operation '{op}': {e}")
        raise RuntimeError(f"Unknown operator '{op}'")

    def _eval_UnaryExpr(self, node):
        val = self._eval(node.operand)
        if node.op == '-':
            return -val
        if node.op == 'not':
            return not self._truthy(val)
        raise RuntimeError(f"Unknown unary operator '{node.op}'")

    def _eval_CallExpr(self, node):
        func = self.env.get(node.callee)
        if not isinstance(func, NoveLangFunction):
            raise RuntimeError(f"'{node.callee}' is not a callable function")
        if len(node.args) != len(func.params):
            raise RuntimeError(
                f"Function '{node.callee}' expects {len(func.params)} argument(s), got {len(node.args)}"
            )
        args = [self._eval(a) for a in node.args]
        call_env = Environment(func.closure)
        for pname, aval in zip(func.params, args):
            call_env.set(pname, aval)
        old = self.env
        self.env = call_env
        result = None
        try:
            for s in func.body:
                self._exec(s)
        except ReturnSignal as sig:
            result = sig.value
        self.env = old
        return result

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True
