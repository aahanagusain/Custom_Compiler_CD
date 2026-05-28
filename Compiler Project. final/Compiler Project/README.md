# ⚡ NoveLang — NLP-Integrated AI Compiler

> **Write code in plain English. NoveLang's NLP engine translates it into a custom programming language and compiles it in real-time.**

## 🧠 What is NoveLang?

NoveLang is a complete compiler project that integrates **Natural Language Processing (NLP)** to allow programming in everyday English. The system features:

- **Custom NLP Engine** — Tokenization, POS tagging, intent detection, entity extraction
- **Custom Programming Language** — "NoveLang" with its own syntax (let, show, check, repeat, task, give)
- **Full Compiler Pipeline** — Lexer → Parser → Semantic Analyzer → Interpreter
- **Professional Web IDE** — 4-panel glassmorphism UI with real-time pipeline visualization

## 🚀 Quick Start

```bash
python start.py
```

Then open **http://localhost:5000** in your browser.

## 📝 How It Works

### Write English:
```
create a variable called age and set it to 20
if age is greater than or equal to 18 then
  print "You are an adult!"
otherwise
  print "You are a minor."
end
```

### NoveLang Generates:
```
let age = 20;
check (age >= 18) {
  show "You are an adult!";
} other {
  show "You are a minor.";
}
```

### Output:
```
You are an adult!
```

## 🔧 NoveLang Syntax Reference

| English | NoveLang |
|---------|----------|
| `create a variable called x and set it to 10` | `let x = 10;` |
| `print "hello"` | `show "hello";` |
| `if x is greater than 5 then` | `check (x > 5) {` |
| `otherwise` | `} other {` |
| `loop from 1 to 10` | `repeat (i : 1 -> 10) {` |
| `while x is less than 100` | `repeat while (x < 100) {` |
| `define a function called greet that takes name` | `task greet(name) {` |
| `return answer` | `give answer;` |
| `end` | `}` |

## 🏗️ Architecture

```
English Input
     ↓
┌─────────────┐
│  NLP Engine  │  Tokenize → POS Tag → Detect Intent → Extract Entities
└──────┬──────┘
       ↓
NoveLang Source Code
       ↓
┌──────┴──────┐
│    Lexer     │  Source → Token Stream
└──────┬──────┘
       ↓
┌──────┴──────┐
│   Parser     │  Tokens → Abstract Syntax Tree (AST)
└──────┬──────┘
       ↓
┌──────┴──────┐
│  Semantic    │  Scope Analysis + Type Inference
│  Analyzer    │
└──────┬──────┘
       ↓
┌──────┴──────┐
│ Interpreter  │  AST → Execution → Output
└─────────────┘
```

## 📁 Project Structure

```
├── backend/
│   ├── server.py           # Flask API server
│   ├── nlp_engine.py       # NLP translation engine
│   ├── lexer.py            # Tokenizer
│   ├── parser_engine.py    # Recursive-descent parser
│   ├── semantic.py         # Semantic analyzer
│   ├── interpreter.py      # AST interpreter
│   ├── pipeline.py         # Pipeline orchestrator
│   └── requirements.txt
├── frontend/
│   ├── index.html          # Main UI
│   ├── css/style.css       # Premium dark theme
│   └── js/app.js           # Frontend logic
├── start.py                # One-click launcher
└── README.md
```

## 🎨 Features

- **4-Panel IDE Layout** — English Input, NoveLang Code, Analysis, Program Output
- **Pipeline Visualizer** — Animated stage-by-stage compilation progress
- **NLP Analysis View** — See POS tags, intents, entities, confidence scores
- **Token Stream** — Visual token chips with types
- **AST Tree** — Interactive Abstract Syntax Tree visualization
- **Semantic Analysis** — Symbol table, type inference, error/warning reports
- **7 Example Programs** — Hello World, Calculator, Fibonacci, FizzBuzz, etc.
- **Syntax Highlighting** — Color-coded NoveLang output
- **Keyboard Shortcut** — Ctrl+Enter to Run All

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **NLP:** Custom-built engine (no external NLP libraries)
- **Compiler:** Hand-written lexer, recursive-descent parser, tree-walking interpreter
