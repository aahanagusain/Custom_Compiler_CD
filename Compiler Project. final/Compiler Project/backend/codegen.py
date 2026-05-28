"""
NoveLang Code Generator
Generates clean, readable NoveLang source code from an AST.
"""

from parser_engine import (
    Program, LetStmt, AssignStmt, ShowStmt, CheckStmt,
    RepeatRangeStmt, RepeatWhileStmt, TaskStmt, GiveStmt, InputStmt,
    BinaryExpr, UnaryExpr, CallExpr, Identifier, NumberLit, StringLit, BoolLit
)

class CodeGenerator:
    def __init__(self):
        self.indent_level = 0

    def generate(self, node):
        return self._to_source(node)

    def _indent(self, text):
        lines = text.split('\n')
        indented_lines = []
        for line in lines:
            if line.strip():
                indented_lines.append("  " * self.indent_level + line)
            else:
                indented_lines.append("")
        return '\n'.join(indented_lines)

    def _to_source(self, node):
        method_name = f'_gen_{type(node).__name__}'
        generator = getattr(self, method_name, None)
        if generator:
            return generator(node)
        raise RuntimeError(f"No code generator for AST node: {type(node).__name__}")

    def _gen_Program(self, node):
        return '\n'.join(self._to_source(stmt) for stmt in node.stmts)

    def _gen_LetStmt(self, node):
        return f"let {node.name} = {self._to_source(node.value)};"

    def _gen_AssignStmt(self, node):
        return f"{node.name} = {self._to_source(node.value)};"

    def _gen_ShowStmt(self, node):
        return f"show {self._to_source(node.value)};"

    def _gen_CheckStmt(self, node):
        cond = self._to_source(node.cond)
        
        self.indent_level += 1
        body_stmts = []
        for s in node.body:
            body_stmts.append(self._indent(self._to_source(s)))
        body_str = '\n'.join(body_stmts)
        self.indent_level -= 1
        
        res = f"check ({cond}) {{\n{body_str}\n" + "  " * self.indent_level + "}"
        
        if node.else_body:
            self.indent_level += 1
            else_stmts = []
            for s in node.else_body:
                else_stmts.append(self._indent(self._to_source(s)))
            else_str = '\n'.join(else_stmts)
            self.indent_level -= 1
            res += f" other {{\n{else_str}\n" + "  " * self.indent_level + "}"
            
        return res

    def _gen_RepeatRangeStmt(self, node):
        start = self._to_source(node.start)
        end = self._to_source(node.end)
        
        self.indent_level += 1
        body_stmts = []
        for s in node.body:
            body_stmts.append(self._indent(self._to_source(s)))
        body_str = '\n'.join(body_stmts)
        self.indent_level -= 1
        
        return f"repeat ({node.var} : {start} -> {end}) {{\n{body_str}\n" + "  " * self.indent_level + "}"

    def _gen_RepeatWhileStmt(self, node):
        cond = self._to_source(node.cond)
        
        self.indent_level += 1
        body_stmts = []
        for s in node.body:
            body_stmts.append(self._indent(self._to_source(s)))
        body_str = '\n'.join(body_stmts)
        self.indent_level -= 1
        
        return f"repeat while ({cond}) {{\n{body_str}\n" + "  " * self.indent_level + "}"

    def _gen_TaskStmt(self, node):
        params = ', '.join(node.params)
        
        self.indent_level += 1
        body_stmts = []
        for s in node.body:
            body_stmts.append(self._indent(self._to_source(s)))
        body_str = '\n'.join(body_stmts)
        self.indent_level -= 1
        
        return f"task {node.name}({params}) {{\n{body_str}\n" + "  " * self.indent_level + "}"

    def _gen_GiveStmt(self, node):
        return f"give {self._to_source(node.value)};"

    def _gen_InputStmt(self, node):
        return f"input {node.name};"

    def _gen_BinaryExpr(self, node):
        return f"({self._to_source(node.left)} {node.op} {self._to_source(node.right)})"

    def _gen_UnaryExpr(self, node):
        op = node.op
        if op == 'not':
            op = 'not '
        return f"({op}{self._to_source(node.operand)})"

    def _gen_CallExpr(self, node):
        args = ', '.join(self._to_source(arg) for arg in node.args)
        return f"{node.callee}({args})"

    def _gen_Identifier(self, node):
        return node.name

    def _gen_NumberLit(self, node):
        return str(node.value)

    def _gen_StringLit(self, node):
        # Escape quotes inside the string representation
        escaped = node.value.replace('"', '\\"')
        return f'"{escaped}"'

    def _gen_BoolLit(self, node):
        return 'true' if node.value else 'false'
