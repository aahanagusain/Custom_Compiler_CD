"""
NoveLang AST Optimizer
Performs constant folding, algebraic simplification, and dead-code elimination.
"""

from parser_engine import (
    Program, LetStmt, AssignStmt, ShowStmt, CheckStmt,
    RepeatRangeStmt, RepeatWhileStmt, TaskStmt, GiveStmt, InputStmt,
    BinaryExpr, UnaryExpr, CallExpr, Identifier, NumberLit, StringLit, BoolLit
)

class Optimizer:
    def __init__(self):
        self.env = {}
        self.usage_counts = {}

    def optimize(self, node):
        node = self._opt(node)
        if isinstance(node, Program):
            node = self._eliminate_dead_vars(node)
        return node

    def _opt(self, node):
        method_name = f'_opt_{type(node).__name__}'
        optimizer = getattr(self, method_name, None)
        if optimizer:
            return optimizer(node)
        return node

    def _opt_Program(self, node):
        new_stmts = []
        for stmt in node.stmts:
            opt_stmt = self._opt(stmt)
            if opt_stmt is not None:
                if isinstance(opt_stmt, list):
                    new_stmts.extend(opt_stmt)
                else:
                    new_stmts.append(opt_stmt)
        node.stmts = new_stmts
        return node

    def _eliminate_dead_vars(self, node):
        if not hasattr(node, 'stmts'):
            return node
            
        def walk_and_remove(stmts):
            new_stmts = []
            for s in stmts:
                if isinstance(s, (LetStmt, AssignStmt)):
                    if self.usage_counts.get(s.name, 0) == 0:
                        continue
                if hasattr(s, 'body') and s.body:
                    s.body = walk_and_remove(s.body)
                if hasattr(s, 'else_body') and s.else_body:
                    s.else_body = walk_and_remove(s.else_body)
                new_stmts.append(s)
            return new_stmts
            
        node.stmts = walk_and_remove(node.stmts)
        return node

    def _opt_Identifier(self, node):
        name = node.name
        # Note: Constant propagation (replacing vars with literals) is disabled 
        # so that calculations remain intact in the optimized code.
        self.usage_counts[name] = self.usage_counts.get(name, 0) + 1
        return node

    def _opt_LetStmt(self, node):
        node.value = self._opt(node.value)
        if type(node.value) in (NumberLit, StringLit, BoolLit):
            self.env[node.name] = node.value
        else:
            if node.name in self.env:
                del self.env[node.name]
        return node

    def _opt_AssignStmt(self, node):
        node.value = self._opt(node.value)
        if type(node.value) in (NumberLit, StringLit, BoolLit):
            self.env[node.name] = node.value
        else:
            if node.name in self.env:
                del self.env[node.name]
        return node

    def _opt_ShowStmt(self, node):
        node.value = self._opt(node.value)
        return node

    def _opt_CheckStmt(self, node):
        cond = self._opt(node.cond)
        
        # Dead code elimination for constant conditions
        if isinstance(cond, BoolLit):
            if cond.value:
                opt_body = []
                for s in node.body:
                    res = self._opt(s)
                    if res is not None:
                        if isinstance(res, list): opt_body.extend(res)
                        else: opt_body.append(res)
                return opt_body
            else:
                opt_else_body = []
                if node.else_body:
                    for s in node.else_body:
                        res = self._opt(s)
                        if res is not None:
                            if isinstance(res, list): opt_else_body.extend(res)
                            else: opt_else_body.append(res)
                    return opt_else_body
                return None

        self.env = {}
        
        opt_body = []
        for s in node.body:
            res = self._opt(s)
            if res is not None:
                if isinstance(res, list):
                    opt_body.extend(res)
                else:
                    opt_body.append(res)
        
        self.env = {}
        opt_else_body = []
        if node.else_body:
            for s in node.else_body:
                res = self._opt(s)
                if res is not None:
                    if isinstance(res, list):
                        opt_else_body.extend(res)
                    else:
                        opt_else_body.append(res)
        
        self.env = {}

        node.cond = cond
        node.body = opt_body
        node.else_body = opt_else_body if node.else_body else None
        return node

    def _opt_RepeatRangeStmt(self, node):
        self.env = {}
        node.start = self._opt(node.start)
        node.end = self._opt(node.end)
        
        opt_body = []
        for s in node.body:
            res = self._opt(s)
            if res is not None:
                if isinstance(res, list):
                    opt_body.extend(res)
                else:
                    opt_body.append(res)
        node.body = opt_body
        self.env = {}
        return node

    def _opt_RepeatWhileStmt(self, node):
        self.env = {}
        cond = self._opt(node.cond)
        
        opt_body = []
        for s in node.body:
            res = self._opt(s)
            if res is not None:
                if isinstance(res, list):
                    opt_body.extend(res)
                else:
                    opt_body.append(res)
        
        # If loop condition is constant false, loop is dead code
        if isinstance(cond, BoolLit) and not cond.value:
            return None
            
        node.cond = cond
        node.body = opt_body
        self.env = {}
        return node

    def _opt_TaskStmt(self, node):
        self.env = {}
        opt_body = []
        for s in node.body:
            res = self._opt(s)
            if res is not None:
                if isinstance(res, list):
                    opt_body.extend(res)
                else:
                    opt_body.append(res)
        node.body = opt_body
        self.env = {}
        return node

    def _opt_GiveStmt(self, node):
        node.value = self._opt(node.value)
        return node

    def _opt_InputStmt(self, node):
        return node

    def _opt_BinaryExpr(self, node):
        left = self._opt(node.left)
        right = self._opt(node.right)
        op = node.op

        # 1. Constant folding
        if type(left) == type(right) and type(left) in (NumberLit, StringLit, BoolLit):
            try:
                val_l = left.value
                val_r = right.value
                
                if op == '+':
                    if isinstance(val_l, str) or isinstance(val_r, str):
                        return StringLit(str(val_l) + str(val_r))
                    return NumberLit(val_l + val_r)
                elif op == '-':
                    return NumberLit(val_l - val_r)
                elif op == '*':
                    return NumberLit(val_l * val_r)
                elif op == '/':
                    if val_r != 0:
                        return NumberLit(val_l / val_r)
                elif op == '%':
                    if val_r != 0:
                        return NumberLit(val_l % val_r)
                elif op == '==':
                    return BoolLit(val_l == val_r)
                elif op == '!=':
                    return BoolLit(val_l != val_r)
                elif op == '>':
                    return BoolLit(val_l > val_r)
                elif op == '<':
                    return BoolLit(val_l < val_r)
                elif op == '>=':
                    return BoolLit(val_l >= val_r)
                elif op == '<=':
                    return BoolLit(val_l <= val_r)
                elif op == 'and':
                    return BoolLit(bool(val_l) and bool(val_r))
                elif op == 'or':
                    return BoolLit(bool(val_l) or bool(val_r))
            except Exception:
                pass

        # 2. Algebraic simplification & Boolean identities
        if op == '+':
            if isinstance(left, NumberLit) and left.value == 0:
                return right
            if isinstance(right, NumberLit) and right.value == 0:
                return left
        elif op == '-':
            if isinstance(right, NumberLit) and right.value == 0:
                return left
        elif op == '*':
            if isinstance(left, NumberLit):
                if left.value == 1:
                    return right
                if left.value == 0:
                    return NumberLit(0)
                if left.value == 2:
                    # Strength reduction: 2 * x -> x + x
                    return BinaryExpr(left=right, op='+', right=right)
            if isinstance(right, NumberLit):
                if right.value == 1:
                    return left
                if right.value == 0:
                    return NumberLit(0)
                if right.value == 2:
                    # Strength reduction: x * 2 -> x + x
                    return BinaryExpr(left=left, op='+', right=left)
        elif op == '/':
            if isinstance(right, NumberLit) and right.value == 1:
                return left
        elif op == 'and':
            if isinstance(left, BoolLit):
                return right if left.value else BoolLit(False)
            if isinstance(right, BoolLit):
                return left if right.value else BoolLit(False)
        elif op == 'or':
            if isinstance(left, BoolLit):
                return BoolLit(True) if left.value else right
            if isinstance(right, BoolLit):
                return BoolLit(True) if right.value else left

        node.left = left
        node.right = right
        return node

    def _opt_UnaryExpr(self, node):
        operand = self._opt(node.operand)
        op = node.op

        if op == '-':
            if isinstance(operand, NumberLit):
                return NumberLit(-operand.value)
        elif op == 'not':
            if isinstance(operand, BoolLit):
                return BoolLit(not operand.value)

        node.operand = operand
        return node

    def _opt_CallExpr(self, node):
        node.args = [self._opt(arg) for arg in node.args]
        return node
