"""
NoveLang Parser — Recursive-descent parser producing an AST.

Grammar:
  program     → stmt*
  stmt        → letStmt | showStmt | checkStmt | repeatStmt
              | taskStmt | giveStmt | inputStmt | block | exprStmt
  letStmt     → LET IDENT '=' expr ';'
  showStmt    → SHOW expr ';'
  checkStmt   → CHECK '(' expr ')' '{' stmt* '}' ( OTHER '{' stmt* '}' )?
  repeatStmt  → REPEAT '(' IDENT ':' expr '->' expr ')' '{' stmt* '}'
              | REPEAT WHILE '(' expr ')' '{' stmt* '}'
  taskStmt    → TASK IDENT '(' params? ')' '{' stmt* '}'
  giveStmt    → GIVE expr ';'
  inputStmt   → INPUT IDENT ';'
  exprStmt    → expr ';'        (includes assignments as  IDENT '=' expr ';')
  expr        → logicOr
  logicOr     → logicAnd ( OR logicAnd )*
  logicAnd    → equality ( AND equality )*
  equality    → comparison ( ('==' | '!=') comparison )*
  comparison  → addition ( ('>' | '<' | '>=' | '<=') addition )*
  addition    → mult ( ('+' | '-') mult )*
  mult        → unary ( ('*' | '/' | '%') unary )*
  unary       → ( NOT | '-' ) unary | call
  call        → primary ( '(' args? ')' )*
  primary     → NUMBER | STRING | TRUE | FALSE | IDENT | '(' expr ')'
"""

from lexer import TokenType


# ─── AST Node Classes ──────────────────────────────────────────────────────────

class ASTNode:
    """Base class for all AST nodes."""
    _node_counter = 0
    def __init__(self):
        ASTNode._node_counter += 1
        self.node_id = f"node_{ASTNode._node_counter}"
    def to_dict(self):
        raise NotImplementedError


class Program(ASTNode):
    def __init__(self, stmts):
        super().__init__()
        self.stmts = stmts
    def to_dict(self):
        return {
            'type': 'Program', 
            'id': self.node_id, 
            'children': [s.to_dict() for s in self.stmts]
        }


class LetStmt(ASTNode):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value
    def to_dict(self):
        return {
            'type': 'LetStatement', 
            'id': self.node_id,
            'name': self.name, 
            'children': [self.value.to_dict()]
        }


class AssignStmt(ASTNode):
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value
    def to_dict(self):
        return {
            'type': 'AssignStatement', 
            'id': self.node_id,
            'name': self.name, 
            'children': [self.value.to_dict()]
        }


class ShowStmt(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    def to_dict(self):
        return {
            'type': 'ShowStatement', 
            'id': self.node_id,
            'children': [self.value.to_dict()]
        }


class CheckStmt(ASTNode):
    def __init__(self, cond, body, else_body=None):
        super().__init__()
        self.cond = cond
        self.body = body
        self.else_body = else_body
    def to_dict(self):
        d = {
            'type': 'CheckStatement', 
            'id': self.node_id,
            'children': [
                {'type': 'Condition', 'children': [self.cond.to_dict()]},
                {'type': 'ThenBlock', 'children': [s.to_dict() for s in self.body]},
            ]
        }
        if self.else_body:
            d['children'].append({'type': 'OtherBlock', 'children': [s.to_dict() for s in self.else_body]})
        return d


class RepeatRangeStmt(ASTNode):
    def __init__(self, var, start, end, body):
        super().__init__()
        self.var = var
        self.start = start
        self.end = end
        self.body = body
    def to_dict(self):
        return {
            'type': 'RepeatRange', 
            'id': self.node_id,
            'variable': self.var, 
            'children': [
                {'type': 'Start', 'children': [self.start.to_dict()]},
                {'type': 'End', 'children': [self.end.to_dict()]},
                {'type': 'Body', 'children': [s.to_dict() for s in self.body]},
            ]
        }


class RepeatWhileStmt(ASTNode):
    def __init__(self, cond, body):
        super().__init__()
        self.cond = cond
        self.body = body
    def to_dict(self):
        return {
            'type': 'RepeatWhile', 
            'id': self.node_id,
            'children': [
                {'type': 'Condition', 'children': [self.cond.to_dict()]},
                {'type': 'Body', 'children': [s.to_dict() for s in self.body]},
            ]
        }


class TaskStmt(ASTNode):
    def __init__(self, name, params, body):
        super().__init__()
        self.name = name
        self.params = params
        self.body = body
    def to_dict(self):
        return {
            'type': 'TaskStatement', 
            'id': self.node_id,
            'name': self.name,
            'params': self.params,
            'children': [s.to_dict() for s in self.body]
        }


class GiveStmt(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    def to_dict(self):
        return {
            'type': 'GiveStatement', 
            'id': self.node_id,
            'children': [self.value.to_dict()]
        }


class InputStmt(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name
    def to_dict(self):
        return {
            'type': 'InputStatement', 
            'id': self.node_id,
            'name': self.name, 
            'children': []
        }


class BinaryExpr(ASTNode):
    def __init__(self, op, left, right):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right
    def to_dict(self):
        return {
            'type': 'BinaryExpr', 
            'id': self.node_id,
            'op': self.op,
            'children': [self.left.to_dict(), self.right.to_dict()]
        }


class UnaryExpr(ASTNode):
    def __init__(self, op, operand):
        super().__init__()
        self.op = op
        self.operand = operand
    def to_dict(self):
        return {
            'type': 'UnaryExpr', 
            'id': self.node_id,
            'op': self.op, 
            'children': [self.operand.to_dict()]
        }


class CallExpr(ASTNode):
    def __init__(self, callee, args):
        super().__init__()
        self.callee = callee
        self.args = args
    def to_dict(self):
        return {
            'type': 'CallExpr', 
            'id': self.node_id,
            'callee': self.callee,
            'children': [a.to_dict() for a in self.args]
        }


class Identifier(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name
    def to_dict(self):
        return {
            'type': 'Identifier', 
            'id': self.node_id,
            'value': self.name, 
            'children': []
        }


class NumberLit(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    def to_dict(self):
        return {
            'type': 'NumberLiteral', 
            'id': self.node_id,
            'value': self.value, 
            'children': []
        }


class StringLit(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    def to_dict(self):
        return {
            'type': 'StringLiteral', 
            'id': self.node_id,
            'value': self.value, 
            'children': []
        }


class BoolLit(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    def to_dict(self):
        return {
            'type': 'BoolLiteral', 
            'id': self.node_id,
            'value': self.value, 
            'children': []
        }


# ─── Parser ────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, message, token=None):
        super().__init__(message)
        self.token = token


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _cur(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def _at(self, *types):
        return self._cur().type in types

    def _eat(self, ttype, msg=''):
        tok = self._cur()
        if tok.type != ttype:
            raise ParseError(msg or f"Expected {ttype} but got {tok.type} ('{tok.value}') at L{tok.line}:{tok.col}", tok)
        self.pos += 1
        return tok

    def _match(self, *types):
        if self._cur().type in types:
            tok = self._cur()
            self.pos += 1
            return tok
        return None

    # ── Entry ───────────────────────────────────────────────────────────────

    def parse(self):
        stmts = []
        while not self._at(TokenType.EOF):
            if self._at(TokenType.COMMENT):
                self.pos += 1
                continue
            stmts.append(self._stmt())
        return Program(stmts)

    # ── Statements ──────────────────────────────────────────────────────────

    def _stmt(self):
        if self._at(TokenType.LET):
            return self._let_stmt()
        if self._at(TokenType.SHOW):
            return self._show_stmt()
        if self._at(TokenType.CHECK):
            return self._check_stmt()
        if self._at(TokenType.REPEAT):
            return self._repeat_stmt()
        if self._at(TokenType.TASK):
            return self._task_stmt()
        if self._at(TokenType.GIVE):
            return self._give_stmt()
        if self._at(TokenType.INPUT):
            return self._input_stmt()
        # Assignment or expression statement
        return self._expr_stmt()

    def _let_stmt(self):
        self._eat(TokenType.LET)
        name_tok = self._eat(TokenType.IDENTIFIER, "Expected variable name after 'let'")
        self._eat(TokenType.EQUALS, "Expected '=' after variable name")
        value = self._expr()
        self._eat(TokenType.SEMI, "Expected ';' after variable declaration")
        return LetStmt(name_tok.value, value)

    def _show_stmt(self):
        self._eat(TokenType.SHOW)
        value = self._expr()
        self._eat(TokenType.SEMI, "Expected ';' after show statement")
        return ShowStmt(value)

    def _check_stmt(self):
        self._eat(TokenType.CHECK)
        self._eat(TokenType.LPAREN, "Expected '(' after 'check'")
        cond = self._expr()
        self._eat(TokenType.RPAREN, "Expected ')' after condition")
        self._eat(TokenType.LBRACE, "Expected '{' to open then-block")
        body = self._block_stmts()
        self._eat(TokenType.RBRACE, "Expected '}' to close then-block")
        else_body = None
        if self._match(TokenType.OTHER):
            self._eat(TokenType.LBRACE, "Expected '{' after 'other'")
            else_body = self._block_stmts()
            self._eat(TokenType.RBRACE, "Expected '}' to close other-block")
        return CheckStmt(cond, body, else_body)

    def _repeat_stmt(self):
        self._eat(TokenType.REPEAT)
        if self._match(TokenType.WHILE):
            self._eat(TokenType.LPAREN, "Expected '(' after 'repeat while'")
            cond = self._expr()
            self._eat(TokenType.RPAREN, "Expected ')' after while condition")
            self._eat(TokenType.LBRACE, "Expected '{'")
            body = self._block_stmts()
            self._eat(TokenType.RBRACE, "Expected '}'")
            return RepeatWhileStmt(cond, body)
        self._eat(TokenType.LPAREN, "Expected '('")
        var_tok = self._eat(TokenType.IDENTIFIER, "Expected loop variable")
        self._eat(TokenType.COLON, "Expected ':'")
        start = self._expr()
        self._eat(TokenType.ARROW, "Expected '->'")
        end = self._expr()
        self._eat(TokenType.RPAREN, "Expected ')'")
        self._eat(TokenType.LBRACE, "Expected '{'")
        body = self._block_stmts()
        self._eat(TokenType.RBRACE, "Expected '}'")
        return RepeatRangeStmt(var_tok.value, start, end, body)

    def _task_stmt(self):
        self._eat(TokenType.TASK)
        name_tok = self._eat(TokenType.IDENTIFIER, "Expected function name")
        self._eat(TokenType.LPAREN, "Expected '('")
        params = []
        if not self._at(TokenType.RPAREN):
            params.append(self._eat(TokenType.IDENTIFIER, "Expected parameter name").value)
            while self._match(TokenType.COMMA):
                params.append(self._eat(TokenType.IDENTIFIER, "Expected parameter name").value)
        self._eat(TokenType.RPAREN, "Expected ')'")
        self._eat(TokenType.LBRACE, "Expected '{'")
        body = self._block_stmts()
        self._eat(TokenType.RBRACE, "Expected '}'")
        return TaskStmt(name_tok.value, params, body)

    def _give_stmt(self):
        self._eat(TokenType.GIVE)
        value = self._expr()
        self._eat(TokenType.SEMI, "Expected ';' after give statement")
        return GiveStmt(value)

    def _input_stmt(self):
        self._eat(TokenType.INPUT)
        name_tok = self._eat(TokenType.IDENTIFIER, "Expected variable name")
        self._eat(TokenType.SEMI, "Expected ';'")
        return InputStmt(name_tok.value)

    def _expr_stmt(self):
        expr = self._expr()
        # Check for assignment: if expr is an Identifier followed by '='
        if isinstance(expr, Identifier) and self._match(TokenType.EQUALS):
            value = self._expr()
            self._eat(TokenType.SEMI, "Expected ';' after assignment")
            return AssignStmt(expr.name, value)
        self._eat(TokenType.SEMI, "Expected ';' after expression")
        return expr  # bare expression statement

    def _block_stmts(self):
        stmts = []
        while not self._at(TokenType.RBRACE) and not self._at(TokenType.EOF):
            if self._at(TokenType.COMMENT):
                self.pos += 1
                continue
            stmts.append(self._stmt())
        return stmts

    # ── Expressions (precedence climbing) ───────────────────────────────────

    def _expr(self):
        return self._logic_or()

    def _logic_or(self):
        left = self._logic_and()
        while self._match(TokenType.OR):
            right = self._logic_and()
            left = BinaryExpr('or', left, right)
        return left

    def _logic_and(self):
        left = self._equality()
        while self._match(TokenType.AND):
            right = self._equality()
            left = BinaryExpr('and', left, right)
        return left

    def _equality(self):
        left = self._comparison()
        while True:
            tok = self._match(TokenType.EQEQ, TokenType.NEQ)
            if not tok:
                break
            right = self._comparison()
            left = BinaryExpr(tok.value, left, right)
        return left

    def _comparison(self):
        left = self._addition()
        while True:
            tok = self._match(TokenType.GT, TokenType.LT, TokenType.GEQ, TokenType.LEQ)
            if not tok:
                break
            right = self._addition()
            left = BinaryExpr(tok.value, left, right)
        return left

    def _addition(self):
        left = self._multiplication()
        while True:
            tok = self._match(TokenType.PLUS, TokenType.MINUS)
            if not tok:
                break
            right = self._multiplication()
            left = BinaryExpr(tok.value, left, right)
        return left

    def _multiplication(self):
        left = self._unary()
        while True:
            tok = self._match(TokenType.STAR, TokenType.SLASH, TokenType.MODULO)
            if not tok:
                break
            right = self._unary()
            left = BinaryExpr(tok.value, left, right)
        return left

    def _unary(self):
        if self._match(TokenType.NOT):
            return UnaryExpr('not', self._unary())
        tok = self._match(TokenType.MINUS)
        if tok:
            return UnaryExpr('-', self._unary())
        return self._call()

    def _call(self):
        expr = self._primary()
        while self._match(TokenType.LPAREN):
            args = []
            if not self._at(TokenType.RPAREN):
                args.append(self._expr())
                while self._match(TokenType.COMMA):
                    args.append(self._expr())
            self._eat(TokenType.RPAREN, "Expected ')' after arguments")
            if isinstance(expr, Identifier):
                expr = CallExpr(expr.name, args)
            else:
                raise ParseError("Can only call functions by name")
        return expr

    def _primary(self):
        tok = self._cur()
        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberLit(tok.value)
        if tok.type == TokenType.STRING:
            self.pos += 1
            return StringLit(tok.value)
        if tok.type == TokenType.TRUE:
            self.pos += 1
            return BoolLit(True)
        if tok.type == TokenType.FALSE:
            self.pos += 1
            return BoolLit(False)
        if tok.type == TokenType.IDENTIFIER:
            self.pos += 1
            return Identifier(tok.value)
        if tok.type == TokenType.LPAREN:
            self.pos += 1
            expr = self._expr()
            self._eat(TokenType.RPAREN, "Expected closing ')'")
            return expr
        raise ParseError(f"Unexpected token {tok.type} ('{tok.value}') at L{tok.line}:{tok.col}", tok)
