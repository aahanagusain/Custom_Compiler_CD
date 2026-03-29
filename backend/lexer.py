"""
NoveLang Lexer — Tokenizer for the NoveLang language.
Converts raw NoveLang source code into a stream of typed tokens.
"""


# ─── Token Types ────────────────────────────────────────────────────────────────

class TokenType:
    # Keywords
    LET      = 'LET'
    SHOW     = 'SHOW'
    CHECK    = 'CHECK'
    OTHER    = 'OTHER'
    REPEAT   = 'REPEAT'
    WHILE    = 'WHILE'
    TASK     = 'TASK'
    GIVE     = 'GIVE'
    INPUT    = 'INPUT'
    AND      = 'AND'
    OR       = 'OR'
    NOT      = 'NOT'
    TRUE     = 'TRUE'
    FALSE    = 'FALSE'
    # Literals
    NUMBER   = 'NUMBER'
    STRING   = 'STRING'
    IDENTIFIER = 'IDENTIFIER'
    # Operators
    PLUS     = 'PLUS'
    MINUS    = 'MINUS'
    STAR     = 'STAR'
    SLASH    = 'SLASH'
    MODULO   = 'MODULO'
    EQEQ     = 'EQEQ'
    NEQ      = 'NEQ'
    GEQ      = 'GEQ'
    LEQ      = 'LEQ'
    GT       = 'GT'
    LT       = 'LT'
    EQUALS   = 'EQUALS'
    # Delimiters
    LPAREN   = 'LPAREN'
    RPAREN   = 'RPAREN'
    LBRACE   = 'LBRACE'
    RBRACE   = 'RBRACE'
    SEMI     = 'SEMI'
    COMMA    = 'COMMA'
    COLON    = 'COLON'
    ARROW    = 'ARROW'
    # Special
    COMMENT  = 'COMMENT'
    EOF      = 'EOF'
    ERROR    = 'ERROR'


KEYWORDS = {
    'let':    TokenType.LET,
    'show':   TokenType.SHOW,
    'check':  TokenType.CHECK,
    'other':  TokenType.OTHER,
    'repeat': TokenType.REPEAT,
    'while':  TokenType.WHILE,
    'task':   TokenType.TASK,
    'give':   TokenType.GIVE,
    'input':  TokenType.INPUT,
    'and':    TokenType.AND,
    'or':     TokenType.OR,
    'not':    TokenType.NOT,
    'true':   TokenType.TRUE,
    'false':  TokenType.FALSE,
}


class Token:
    __slots__ = ('type', 'value', 'line', 'col')

    def __init__(self, type, value, line=0, col=0):
        self.type  = type
        self.value = value
        self.line  = line
        self.col   = col

    def to_dict(self):
        return {'type': self.type, 'value': self.value, 'line': self.line, 'col': self.col}

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, L{self.line}:{self.col})'


# ─── Lexer ──────────────────────────────────────────────────────────────────────

class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col  = col


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.col    = 1
        self.tokens = []

    def tokenize(self):
        """Tokenize the full source and return list of Token objects."""
        self.tokens = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            # Whitespace
            if ch in ' \t\r':
                self._advance()
                continue
            if ch == '\n':
                self._advance()
                self.line += 1
                self.col = 1
                continue

            # Comments  // ...
            if ch == '/' and self._peek(1) == '/':
                start_col = self.col
                self._advance()  # skip first /
                self._advance()  # skip second /
                comment = ''
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    comment += self.source[self.pos]
                    self._advance()
                self.tokens.append(Token(TokenType.COMMENT, comment.strip(), self.line, start_col))
                continue

            # Strings
            if ch in ('"', "'"):
                self._read_string(ch)
                continue

            # Numbers
            if ch.isdigit() or (ch == '-' and self._peek(1) and self._peek(1).isdigit() and self._prev_allows_negative()):
                self._read_number()
                continue

            # Two-char operators
            two = self.source[self.pos:self.pos + 2]
            if two == '==':
                self.tokens.append(Token(TokenType.EQEQ, '==', self.line, self.col))
                self._advance(); self._advance()
                continue
            if two == '!=':
                self.tokens.append(Token(TokenType.NEQ, '!=', self.line, self.col))
                self._advance(); self._advance()
                continue
            if two == '>=':
                self.tokens.append(Token(TokenType.GEQ, '>=', self.line, self.col))
                self._advance(); self._advance()
                continue
            if two == '<=':
                self.tokens.append(Token(TokenType.LEQ, '<=', self.line, self.col))
                self._advance(); self._advance()
                continue
            if two == '->':
                self.tokens.append(Token(TokenType.ARROW, '->', self.line, self.col))
                self._advance(); self._advance()
                continue

            # Single-char operators & delimiters
            single_map = {
                '+': TokenType.PLUS,   '-': TokenType.MINUS,
                '*': TokenType.STAR,   '/': TokenType.SLASH,
                '%': TokenType.MODULO, '>': TokenType.GT,
                '<': TokenType.LT,     '=': TokenType.EQUALS,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                ';': TokenType.SEMI,   ',': TokenType.COMMA,
                ':': TokenType.COLON,
            }
            if ch in single_map:
                self.tokens.append(Token(single_map[ch], ch, self.line, self.col))
                self._advance()
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == '_':
                self._read_identifier()
                continue

            # Unknown character
            self.tokens.append(Token(TokenType.ERROR, ch, self.line, self.col))
            self._advance()

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _advance(self):
        self.pos += 1
        self.col += 1

    def _peek(self, offset=1):
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else None

    def _prev_allows_negative(self):
        if not self.tokens:
            return True
        last = self.tokens[-1].type
        return last in (TokenType.EQUALS, TokenType.LPAREN, TokenType.COMMA,
                        TokenType.SEMI, TokenType.LBRACE, TokenType.ARROW,
                        TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
                        TokenType.SLASH, TokenType.MODULO, TokenType.EQEQ,
                        TokenType.NEQ, TokenType.GT, TokenType.LT,
                        TokenType.GEQ, TokenType.LEQ, TokenType.AND,
                        TokenType.OR, TokenType.NOT, TokenType.COLON)

    def _read_string(self, quote):
        start_col = self.col
        self._advance()  # skip opening quote
        value = ''
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\' and self._peek(1):
                value += self.source[self.pos + 1]
                self._advance()
                self._advance()
            else:
                value += self.source[self.pos]
                self._advance()
        if self.pos < len(self.source):
            self._advance()  # skip closing quote
        self.tokens.append(Token(TokenType.STRING, value, self.line, start_col))

    def _read_number(self):
        start_col = self.col
        num = ''
        if self.source[self.pos] == '-':
            num += '-'
            self._advance()
        has_dot = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or (self.source[self.pos] == '.' and not has_dot)):
            if self.source[self.pos] == '.':
                has_dot = True
            num += self.source[self.pos]
            self._advance()
        self.tokens.append(Token(TokenType.NUMBER, float(num) if has_dot else int(num), self.line, start_col))

    def _read_identifier(self):
        start_col = self.col
        ident = ''
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            ident += self.source[self.pos]
            self._advance()
        tt = KEYWORDS.get(ident.lower(), TokenType.IDENTIFIER)
        self.tokens.append(Token(tt, ident if tt == TokenType.IDENTIFIER else ident.lower(), self.line, start_col))
