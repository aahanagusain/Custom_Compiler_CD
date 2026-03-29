"""
NoveLang NLP Engine
Translates natural English instructions into NoveLang source code.
Pipeline: Tokenization -> POS Tagging -> Intent Detection -> Entity Extraction -> Code Generation
"""

import re


# ─── Simple POS Tagger ─────────────────────────────────────────────────────────

DETERMINERS = {'a', 'an', 'the', 'this', 'that', 'these', 'those', 'my', 'your', 'its'}
PREPOSITIONS = {'in', 'on', 'at', 'to', 'from', 'with', 'by', 'for', 'of', 'into', 'as', 'than'}
CONJUNCTIONS = {'and', 'or', 'but', 'then', 'so', 'yet'}
PRONOUNS = {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
CODE_VERBS = {
    'create', 'make', 'define', 'declare', 'set', 'let', 'store', 'save', 'put',
    'print', 'display', 'show', 'output', 'write', 'say', 'log',
    'loop', 'repeat', 'iterate', 'count', 'go',
    'check', 'compare', 'test', 'verify',
    'call', 'run', 'execute', 'invoke',
    'return', 'give', 'send',
    'add', 'subtract', 'multiply', 'divide',
    'increment', 'decrement', 'increase', 'decrease',
    'ask', 'get', 'read', 'take', 'accept', 'input',
    'end', 'stop', 'done', 'finish',
    'initialize', 'assign', 'update', 'change', 'modify',
}
CODE_NOUNS = {
    'variable', 'var', 'value', 'number', 'string', 'text',
    'function', 'method', 'procedure', 'routine',
    'result', 'answer', 'output', 'input', 'user',
    'loop', 'condition', 'block', 'parameter', 'argument',
    'name', 'item', 'element', 'list', 'array',
}
ADJECTIVES_KW = {
    'greater', 'less', 'equal', 'big', 'small', 'large',
    'true', 'false', 'each', 'every', 'new', 'old',
}


def pos_tag_word(word):
    w = word.lower()
    if w in DETERMINERS:
        return 'Determiner'
    if w in PREPOSITIONS:
        return 'Preposition'
    if w in CONJUNCTIONS:
        return 'Conjunction'
    if w in PRONOUNS:
        return 'Pronoun'
    if w in CODE_VERBS:
        return 'Verb'
    if w in CODE_NOUNS:
        return 'Noun'
    if w in ADJECTIVES_KW:
        return 'Adjective'
    if re.match(r'^-?\d+(\.\d+)?$', w):
        return 'Number'
    if w.startswith('"') or w.startswith("'"):
        return 'String'
    if w in ('not', 'no', 'never'):
        return 'Negation'
    if w in ('is', 'are', 'was', 'were', 'be', 'been', 'being', 'equals'):
        return 'Auxiliary'
    if w.endswith('ly'):
        return 'Adverb'
    return 'Noun'


def tokenize_line(line):
    tokens = []
    i = 0
    while i < len(line):
        if line[i] in ' \t':
            i += 1
            continue
        if line[i] in ('"', "'"):
            q = line[i]
            j = i + 1
            while j < len(line) and line[j] != q:
                j += 1
            tokens.append(line[i:j + 1] if j < len(line) else line[i:])
            i = j + 1
            continue
        j = i
        while j < len(line) and line[j] not in ' \t':
            j += 1
        tokens.append(line[i:j])
        i = j
    return tokens


# ─── Expression Translator ─────────────────────────────────────────────────────

def translate_expression(text):
    """Convert English math/logic expressions to NoveLang expressions."""
    text = text.strip().rstrip('.')
    # Comparison operators (order matters - longer first)
    text = re.sub(r'\bis\s+greater\s+than\s+or\s+equal\s+to\b', '>=', text)
    text = re.sub(r'\bis\s+less\s+than\s+or\s+equal\s+to\b', '<=', text)
    text = re.sub(r'\bis\s+greater\s+than\b', '>', text)
    text = re.sub(r'\bis\s+less\s+than\b', '<', text)
    text = re.sub(r'\bis\s+equal\s+to\b', '==', text)
    text = re.sub(r'\bis\s+not\s+equal\s+to\b', '!=', text)
    text = re.sub(r'\bequals\b', '==', text)
    text = re.sub(r'\bnot\s+equals\b', '!=', text)
    text = re.sub(r'\bdoes\s+not\s+equal\b', '!=', text)
    # Math operators
    text = re.sub(r'\bplus\b', '+', text)
    text = re.sub(r'\bminus\b', '-', text)
    text = re.sub(r'\btimes\b', '*', text)
    text = re.sub(r'\bmultiplied\s+by\b', '*', text)
    text = re.sub(r'\bdivided\s+by\b', '/', text)
    text = re.sub(r'\bmodulo\b', '%', text)
    text = re.sub(r'\bremainder\s+of\b', '%', text)
    # Logic
    text = re.sub(r'\band\b', 'and', text)
    text = re.sub(r'\bor\b', 'or', text)
    text = re.sub(r'\bnot\b', 'not', text)
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_value(text):
    """Extract a value - could be a number, string, boolean, or expression."""
    text = text.strip().rstrip('.;')
    if re.match(r'^-?\d+(\.\d+)?$', text):
        return text
    if text.lower() in ('true', 'false'):
        return text.lower()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text
    if re.match(r'^[a-zA-Z_]\w*$', text):
        return text
    return translate_expression(text)


# ─── Intent Patterns ───────────────────────────────────────────────────────────

INTENT_PATTERNS = {
    'variable_declaration': [
        (r'(?:create|make|define|declare)\s+(?:a\s+)?(?:new\s+)?(?:variable|var)\s+(?:called|named)\s+(\w+)\s+(?:and\s+)?(?:set|assign|give|initialize)?\s*(?:it\s+)?(?:to|as|with|equals?|=|value)\s+(.+)', 0.95),
        (r'(?:create|make|define|declare)\s+(?:a\s+)?(?:new\s+)?(?:variable|var)\s+(\w+)\s+(?:as|=|to|with)\s+(.+)', 0.93),
        (r'(?:let)\s+(\w+)\s+(?:be|equal\s+to|to|=|as)\s+(.+)', 0.90),
        (r'(?:set)\s+(\w+)\s+(?:be|equal\s+to|to|=|as)\s+(.+)', 0.85),
        (r'(?:store|save|put)\s+(.+?)\s+(?:in|into|as)\s+(?:a\s+)?(?:variable\s+)?(?:called\s+)?(\w+)', 0.88),
        (r'(?:initialize|init)\s+(\w+)\s+(?:to|as|with|=)\s+(.+)', 0.90),
        (r'(\w+)\s+(?:is|=)\s+(.+)', 0.60),
    ],
    'print': [
        (r'(?:print|display|show|output|write|say|log)\s+"(.+?)"', 0.96),
        (r"(?:print|display|show|output|write|say|log)\s+'(.+?)'", 0.96),
        (r'(?:print|display|show|output|write|say|log)\s+(?:the\s+)?(?:value\s+of\s+)?(.+)', 0.90),
    ],
    'if_start': [
        (r'(?:if|when|check\s+if|check\s+whether|in\s+case)\s+(.+?)\s+(?:then|do|,)\s*$', 0.95),
        (r'(?:if|when|check\s+if|check\s+whether)\s+(.+)', 0.90),
    ],
    'else_clause': [
        (r'^(?:otherwise|else|or\s+else|if\s+not)\s*$', 0.95),
    ],
    'end_block': [
        (r'^(?:end|done|stop|finish|end\s+if|end\s+loop|end\s+function|end\s+block|close)\s*$', 0.95),
    ],
    'loop_range': [
        (r'(?:loop|repeat|iterate|count|go)\s+(?:from\s+)?(\w+)\s+(?:to|until|through)\s+(\w+)', 0.93),
        (r'(?:for\s+each|for\s+every)\s+(?:number|value|item)\s+(?:from\s+)?(\w+)\s+(?:to|until)\s+(\w+)', 0.93),
    ],
    'while_loop': [
        (r'(?:while|as\s+long\s+as|keep\s+going\s+while|repeat\s+while|keep\s+looping\s+while)\s+(.+)', 0.93),
    ],
    'function_def': [
        (r'(?:define|create|make|declare)\s+(?:a\s+)?(?:new\s+)?function\s+(?:called|named)\s+(\w+)\s+(?:that\s+)?(?:takes?|with|accepts?)\s+(?:parameters?\s+)?(.+)', 0.93),
        (r'(?:define|create|make|declare)\s+(?:a\s+)?(?:new\s+)?function\s+(?:called|named)\s+(\w+)', 0.90),
    ],
    'function_call': [
        (r'(?:call|run|execute|invoke)\s+(?:function\s+)?(\w+)\s+(?:with|using|passing)\s+(.+)', 0.93),
        (r'(?:call|run|execute|invoke)\s+(?:function\s+)?(\w+)', 0.90),
    ],
    'return_stmt': [
        (r'(?:return|give\s+back|send\s+back)\s+(.+)', 0.93),
        (r'(?:give|yield)\s+(.+)', 0.90),
    ],
    'input_stmt': [
        (r'(?:ask|get|read|take|accept)\s+(?:the\s+)?(?:user\s+)?(?:for\s+)?(?:input\s+)?(?:and\s+)?(?:store\s+)?(?:(?:it\s+)?(?:in|into|as)\s+)?(\w+)', 0.88),
    ],
    'assignment': [
        (r'(?:change|update|modify|set)\s+(\w+)\s+to\s+(.+)', 0.90),
        (r'(?:increment|increase)\s+(\w+)\s+by\s+(.+)', 0.90),
        (r'(?:increment|increase)\s+(\w+)', 0.85),
        (r'(?:decrement|decrease)\s+(\w+)\s+by\s+(.+)', 0.90),
        (r'(?:decrement|decrease)\s+(\w+)', 0.85),
    ],
    'comment': [
        (r'^(?:note|comment|remark)\s*:\s*(.*)', 0.95),
        (r'^(?://|#)\s*(.*)', 0.95),
    ],
}


# ─── NLP Engine ─────────────────────────────────────────────────────────────────

class NLPEngine:
    def __init__(self):
        self.block_stack = []

    def analyze_line(self, line):
        """Perform full NLP analysis on a single English line."""
        tokens = tokenize_line(line)
        pos_tags = [(t, pos_tag_word(t)) for t in tokens]
        intent, confidence, match = self._detect_intent(line)
        entities = self._extract_entities(intent, match, line)
        novelang = self._generate_code(intent, entities, line)
        return {
            'original': line,
            'tokens': tokens,
            'pos_tags': pos_tags,
            'intent': intent,
            'confidence': round(confidence, 2),
            'entities': entities,
            'generated': novelang,
        }

    def translate(self, english_text):
        """Translate full English program to NoveLang."""
        self.block_stack = []
        lines = english_text.strip().split('\n')
        analyses = []
        novelang_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                novelang_lines.append('')
                continue
            analysis = self.analyze_line(stripped)
            analyses.append(analysis)
            novelang_lines.append(analysis['generated'])
        # Close any remaining open blocks
        while self.block_stack:
            self.block_stack.pop()
            novelang_lines.append('}')
        return '\n'.join(novelang_lines), analyses

    # ── Intent Detection ────────────────────────────────────────────────────

    def _detect_intent(self, line):
        line_lower = line.lower().strip().rstrip('.')
        best_intent = 'unknown'
        best_confidence = 0.0
        best_match = None
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern, base_conf in patterns:
                m = re.match(pattern, line_lower, re.IGNORECASE)
                if m and base_conf > best_confidence:
                    best_intent = intent
                    best_confidence = base_conf
                    best_match = m
        return best_intent, best_confidence, best_match

    # ── Entity Extraction ───────────────────────────────────────────────────

    def _extract_entities(self, intent, match, line):
        entities = {}
        if not match:
            return entities
        groups = match.groups()
        if intent == 'variable_declaration':
            if 'store' in line.lower() or 'save' in line.lower() or 'put' in line.lower():
                entities['value'] = groups[0].strip() if len(groups) > 0 else ''
                entities['name'] = groups[1].strip() if len(groups) > 1 else ''
            else:
                entities['name'] = groups[0].strip() if len(groups) > 0 else ''
                entities['value'] = groups[1].strip() if len(groups) > 1 else ''
        elif intent == 'print':
            raw = groups[0].strip() if groups else ''
            # Check if the original line has quotes around this value
            line_lower = line.lower()
            if f'"{raw.lower()}"' in line_lower or f"'{raw.lower()}'" in line_lower:
                entities['value'] = f'"{raw}"'
            else:
                entities['value'] = raw
        elif intent == 'if_start':
            entities['condition'] = groups[0].strip() if groups else ''
        elif intent == 'loop_range':
            entities['start'] = groups[0].strip() if len(groups) > 0 else '1'
            entities['end'] = groups[1].strip() if len(groups) > 1 else '10'
        elif intent == 'while_loop':
            entities['condition'] = groups[0].strip() if groups else ''
        elif intent == 'function_def':
            entities['name'] = groups[0].strip() if len(groups) > 0 else ''
            entities['params'] = groups[1].strip() if len(groups) > 1 and groups[1] else ''
        elif intent == 'function_call':
            entities['name'] = groups[0].strip() if len(groups) > 0 else ''
            entities['args'] = groups[1].strip() if len(groups) > 1 and groups[1] else ''
        elif intent == 'return_stmt':
            entities['value'] = groups[0].strip() if groups else ''
        elif intent == 'input_stmt':
            entities['name'] = groups[0].strip() if groups else ''
        elif intent == 'assignment':
            entities['name'] = groups[0].strip() if len(groups) > 0 else ''
            entities['value'] = groups[1].strip() if len(groups) > 1 and groups[1] else ''
        elif intent == 'comment':
            entities['text'] = groups[0].strip() if groups else ''
        return entities

    # ── Code Generation ─────────────────────────────────────────────────────

    def _generate_code(self, intent, entities, line):
        if intent == 'variable_declaration':
            name = entities.get('name', 'x')
            val = extract_value(entities.get('value', '0'))
            return f'let {name} = {val};'

        elif intent == 'print':
            raw = entities.get('value', '')
            # Already quoted
            if raw.startswith('"') or raw.startswith("'"):
                return f'show {raw};'
            # Check if it's a number, boolean, variable name, or math expression
            val = extract_value(raw)
            # If the extracted value is just a cleaned-up identifier or valid expression, use as-is
            if re.match(r'^-?\d+(\.\d+)?$', val):
                return f'show {val};'
            if val.lower() in ('true', 'false'):
                return f'show {val};'
            if re.match(r'^[a-zA-Z_]\w*$', val):
                return f'show {val};'
            # If it contains operators (+, -, *, /, %, >, <, ==, etc.), it's an expression
            if any(op in val for op in ['+', '-', '*', '/', '%', '>', '<', '==', '!=', 'and', 'or']):
                return f'show {val};'
            # Otherwise wrap as string
            return f'show "{raw}";'

        elif intent == 'if_start':
            cond = translate_expression(entities.get('condition', 'true'))
            self.block_stack.append('if')
            return f'check ({cond}) {{'

        elif intent == 'else_clause':
            return '} other {'

        elif intent == 'end_block':
            if self.block_stack:
                self.block_stack.pop()
            return '}'

        elif intent == 'loop_range':
            s = entities.get('start', '1')
            e = entities.get('end', '10')
            self.block_stack.append('loop')
            return f'repeat (i : {s} -> {e}) {{'

        elif intent == 'while_loop':
            cond = translate_expression(entities.get('condition', 'true'))
            self.block_stack.append('while')
            return f'repeat while ({cond}) {{'

        elif intent == 'function_def':
            name = entities.get('name', 'myFunc')
            params = entities.get('params', '')
            param_list = ', '.join(p.strip() for p in re.split(r'\s+and\s+|\s*,\s*', params) if p.strip()) if params else ''
            self.block_stack.append('function')
            return f'task {name}({param_list}) {{'

        elif intent == 'function_call':
            name = entities.get('name', 'myFunc')
            args = entities.get('args', '')
            arg_list = ', '.join(a.strip() for a in re.split(r'\s+and\s+|\s*,\s*', args) if a.strip()) if args else ''
            return f'{name}({arg_list});'

        elif intent == 'return_stmt':
            val = extract_value(entities.get('value', '0'))
            return f'give {val};'

        elif intent == 'input_stmt':
            name = entities.get('name', 'x')
            return f'input {name};'

        elif intent == 'assignment':
            name = entities.get('name', 'x')
            raw_line = line.lower()
            if 'increment' in raw_line or 'increase' in raw_line:
                val = entities.get('value') or '1'
                return f'{name} = {name} + {extract_value(val)};'
            elif 'decrement' in raw_line or 'decrease' in raw_line:
                val = entities.get('value') or '1'
                return f'{name} = {name} - {extract_value(val)};'
            else:
                val = extract_value(entities.get('value') or '0')
                return f'{name} = {val};'

        elif intent == 'comment':
            text = entities.get('text', '')
            return f'// {text}'

        else:
            return f'// [unrecognized] {line}'
