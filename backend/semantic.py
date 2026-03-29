"""
NoveLang Semantic Analyzer
Performs scope analysis, type inference, and error detection on the AST.
"""

from parser_engine import (
    Program, LetStmt, AssignStmt, ShowStmt, CheckStmt,
    RepeatRangeStmt, RepeatWhileStmt, TaskStmt, GiveStmt, InputStmt,
    BinaryExpr, UnaryExpr, CallExpr, Identifier, NumberLit, StringLit, BoolLit,
)


class Symbol:
    def __init__(self, name, kind, inferred_type='any', scope_depth=0):
        self.name = name
        self.kind = kind                # 'variable', 'function', 'parameter'
        self.inferred_type = inferred_type
        self.scope_depth = scope_depth

    def to_dict(self):
        return {
            'name': self.name,
            'kind': self.kind,
            'inferred_type': self.inferred_type,
            'scope_depth': self.scope_depth,
        }


class Scope:
    def __init__(self, parent=None, depth=0):
        self.symbols = {}
        self.parent = parent
        self.depth = depth

    def define(self, name, kind, inferred_type='any'):
        self.symbols[name] = Symbol(name, kind, inferred_type, self.depth)

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def all_symbols(self):
        syms = list(self.symbols.values())
        if self.parent:
            syms.extend(self.parent.all_symbols())
        return syms


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.scope = Scope()
        self.all_symbols = []

    def analyze(self, ast):
        self.errors = []
        self.warnings = []
        self.info = []
        self.scope = Scope()
        self._visit(ast)
        self.all_symbols = self.scope.all_symbols()
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'symbols': [s.to_dict() for s in self.all_symbols],
            'valid': len(self.errors) == 0,
        }

    def _visit(self, node):
        method = f'_visit_{type(node).__name__}'
        visitor = getattr(self, method, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node):
        pass

    def _visit_Program(self, node):
        for stmt in node.stmts:
            self._visit(stmt)

    def _visit_LetStmt(self, node):
        if self.scope.symbols.get(node.name):
            self.warnings.append(f"Variable '{node.name}' already declared in this scope, will be overwritten")
        vtype = self._infer_type(node.value)
        self.scope.define(node.name, 'variable', vtype)
        self.info.append(f"Declared variable '{node.name}' with inferred type '{vtype}'")
        self._visit(node.value)

    def _visit_AssignStmt(self, node):
        sym = self.scope.lookup(node.name)
        if not sym:
            self.errors.append(f"Assignment to undeclared variable '{node.name}'")
        self._visit(node.value)

    def _visit_ShowStmt(self, node):
        self._visit(node.value)

    def _visit_CheckStmt(self, node):
        self._visit(node.cond)
        ctype = self._infer_type(node.cond)
        if ctype not in ('boolean', 'any'):
            self.warnings.append(f"Condition in 'check' may not be boolean (inferred '{ctype}')")
        child_scope = Scope(self.scope, self.scope.depth + 1)
        old = self.scope
        self.scope = child_scope
        for s in node.body:
            self._visit(s)
        self.scope = old
        if node.else_body:
            child_scope2 = Scope(self.scope, self.scope.depth + 1)
            self.scope = child_scope2
            for s in node.else_body:
                self._visit(s)
            self.scope = old

    def _visit_RepeatRangeStmt(self, node):
        child_scope = Scope(self.scope, self.scope.depth + 1)
        child_scope.define(node.var, 'variable', 'number')
        old = self.scope
        self.scope = child_scope
        self._visit(node.start)
        self._visit(node.end)
        for s in node.body:
            self._visit(s)
        self.scope = old
        self.info.append(f"Loop variable '{node.var}' scoped to repeat block")

    def _visit_RepeatWhileStmt(self, node):
        self._visit(node.cond)
        child_scope = Scope(self.scope, self.scope.depth + 1)
        old = self.scope
        self.scope = child_scope
        for s in node.body:
            self._visit(s)
        self.scope = old

    def _visit_TaskStmt(self, node):
        self.scope.define(node.name, 'function', 'function')
        self.info.append(f"Defined function '{node.name}' with {len(node.params)} parameter(s)")
        child_scope = Scope(self.scope, self.scope.depth + 1)
        for p in node.params:
            child_scope.define(p, 'parameter', 'any')
        old = self.scope
        self.scope = child_scope
        for s in node.body:
            self._visit(s)
        self.scope = old

    def _visit_GiveStmt(self, node):
        self._visit(node.value)

    def _visit_InputStmt(self, node):
        self.scope.define(node.name, 'variable', 'string')
        self.info.append(f"Input variable '{node.name}' will hold user-provided string")

    def _visit_BinaryExpr(self, node):
        self._visit(node.left)
        self._visit(node.right)

    def _visit_UnaryExpr(self, node):
        self._visit(node.operand)

    def _visit_CallExpr(self, node):
        sym = self.scope.lookup(node.callee)
        if not sym:
            self.warnings.append(f"Calling undeclared function '{node.callee}'")
        elif sym.kind != 'function':
            self.errors.append(f"'{node.callee}' is not a function, it's a {sym.kind}")
        for a in node.args:
            self._visit(a)

    def _visit_Identifier(self, node):
        sym = self.scope.lookup(node.name)
        if not sym:
            self.errors.append(f"Use of undeclared identifier '{node.name}'")

    def _visit_NumberLit(self, node):
        pass

    def _visit_StringLit(self, node):
        pass

    def _visit_BoolLit(self, node):
        pass

    # ── Type Inference ──────────────────────────────────────────────────────

    def _infer_type(self, node):
        if isinstance(node, NumberLit):
            return 'number'
        if isinstance(node, StringLit):
            return 'string'
        if isinstance(node, BoolLit):
            return 'boolean'
        if isinstance(node, Identifier):
            sym = self.scope.lookup(node.name)
            return sym.inferred_type if sym else 'any'
        if isinstance(node, BinaryExpr):
            if node.op in ('>', '<', '>=', '<=', '==', '!=', 'and', 'or'):
                return 'boolean'
            lt = self._infer_type(node.left)
            rt = self._infer_type(node.right)
            if lt == 'string' or rt == 'string':
                if node.op == '+':
                    return 'string'
            return 'number'
        if isinstance(node, UnaryExpr):
            if node.op == 'not':
                return 'boolean'
            return 'number'
        if isinstance(node, CallExpr):
            return 'any'
        return 'any'
