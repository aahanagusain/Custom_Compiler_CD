/* ═══════════════════════════════════════════════════════════════
   NoveLang AI Compiler — Main Application Script
   ═══════════════════════════════════════════════════════════════ */

const API = '';   // same-origin

// ── DOM References ──────────────────────────────────────────────
const $  = id  => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const englishInput   = $('english-input');
const novelangOutput = $('novelang-output');
const terminalOutput = $('terminal-output');
const btnTranslate   = $('btn-translate');
const btnCompile     = $('btn-compile');
const btnRunAll      = $('btn-run-all');
const btnClear       = $('btn-clear');
const exampleSelect  = $('example-select');
const statusText     = $('status-text');
const totalTimeEl    = $('total-time');


// ── Tab Switching ──────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const group = tab.closest('.panel');
        group.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        group.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const target = $(tab.getAttribute('data-tab'));
        if (target) target.classList.add('active');
    });
});

// ── Load Examples ──────────────────────────────────────────────
async function loadExampleList() {
    try {
        const res = await fetch(API + '/api/examples');
        const examples = await res.json();
        examples.forEach(ex => {
            const opt = document.createElement('option');
            opt.value = ex.id;
            opt.textContent = `${ex.name}`;
            exampleSelect.appendChild(opt);
        });
    } catch (e) {
        console.warn('Could not load examples:', e);
    }
}

exampleSelect.addEventListener('change', async () => {
    const id = exampleSelect.value;
    if (!id) return;
    try {
        const res = await fetch(API + `/api/examples/${id}`);
        const data = await res.json();
        if (data.success) {
            englishInput.value = data.english;
            resetPipeline();
            novelangOutput.innerHTML = '<span class="placeholder">Click Translate or Run All...</span>';
            termLog('info', `Loaded example: ${data.name}`);
        }
    } catch (e) {
        termLog('error', 'Failed to load example');
    }
});

// ── Pipeline Visualization ─────────────────────────────────────
const stageMap = { nlp: 0, lexer: 1, parser: 2, semantic: 3, interpreter: 4 };
const stageEls = document.querySelectorAll('.pipeline-stage');
const connectorEls = document.querySelectorAll('.pipeline-connector');

function resetPipeline() {
    stageEls.forEach(el => {
        el.classList.remove('active', 'success', 'error');
        el.querySelector('.stage-time').textContent = '';
    });
    connectorEls.forEach(el => el.classList.remove('active'));
}

function setStageActive(name) {
    const idx = stageMap[name];
    if (idx === undefined) return;
    stageEls[idx].classList.add('active');
    stageEls[idx].classList.remove('success', 'error');
}

function setStageSuccess(name, timeMs) {
    const idx = stageMap[name];
    if (idx === undefined) return;
    stageEls[idx].classList.remove('active');
    stageEls[idx].classList.add('success');
    stageEls[idx].querySelector('.stage-time').textContent = `${timeMs}ms`;
    // Activate connector after this stage
    if (idx < connectorEls.length) connectorEls[idx].classList.add('active');
}

function setStageError(name) {
    const idx = stageMap[name];
    if (idx === undefined) return;
    stageEls[idx].classList.remove('active');
    stageEls[idx].classList.add('error');
}

// ── Terminal ───────────────────────────────────────────────────
function termLog(type, text) {
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    line.textContent = text;
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

function termClear() {
    terminalOutput.innerHTML = '<div class="terminal-line system">NoveLang Compiler v1.0 — Ready</div>';
}

// ── Step-by-Step Pipeline ──────────────────────────────────────
const TARGET_STAGES = ['lexer', 'parser', 'semantic', 'interpreter'];
stageEls.forEach(el => {
    el.addEventListener('click', async () => {
        const stage = el.getAttribute('data-stage');
        if (stage === 'nlp') {
            await doTranslate();
        } else {
            // Find index of clicked target
            const targetIdx = TARGET_STAGES.indexOf(stage);
            if (targetIdx !== -1) {
                await doCompileUpTo(targetIdx);
            }
        }
    });
});

let _cachedCompileData = null; // Store last compilation for step-by-step

async function doCompileUpTo(targetIdx) {
    let code = novelangOutput.textContent;
    if (!code || code.includes('will appear here')) {
        termLog('error', 'No NoveLang code to compile. Translate first!');
        return;
    }

    // Always fetch fresh compile dataset to allow code edits in-between
    setStatus('Compiling...');
    termLog('info', 'Executing up to ' + TARGET_STAGES[targetIdx].toUpperCase() + '...');
    try {
        const res = await fetch(API + '/api/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
        });
        const data = await res.json();
        
        // Reset stages from Lexer onwards
        for (let i = 1; i < stageEls.length; i++) {
            stageEls[i].classList.remove('active', 'success', 'error');
            stageEls[i].querySelector('.stage-time').textContent = '';
        }
        for (let i = 0; i < connectorEls.length; i++) {
            connectorEls[i].classList.remove('active');
        }

        const stageKeys = ['lexer', 'parser', 'semantic', 'interpreter'];
        for (let i = 0; i <= targetIdx && i < (data.stages || []).length; i++) {
            const stage = data.stages[i];
            const key = stageKeys[i];
            setStageActive(key);
            await sleep(200);

            if (stage.status === 'error') {
                setStageError(key);
                termLog('error', `${stage.name}: ${stage.error}`);
                break;
            }

            setStageSuccess(key, stage.time_ms);
            termLog('info', `${stage.name}: ${stage.summary}`);

            // Populate analysis tabs based on what succeeded
            if (stage.name === 'Lexer') {
                renderTokens(stage.data);
                document.querySelector('[data-tab="tokens-tab"]').click();
            }
            if (stage.name === 'Parser') {
                renderAST(stage.data);
                document.querySelector('[data-tab="ast-tab"]').click();
            }
            if (stage.name === 'Semantic') {
                renderSemantic(stage.data);
                document.querySelector('[data-tab="semantic-tab"]').click();
            }
            if (stage.name === 'Interpreter' && stage.data) {
                // The interpreter now returns { output, trace }
                const result = stage.data;
                const output = result.output || [];
            }
        }
        setStatus(data.success ? '✓ Step complete' : '✕ Step failed');

    } catch (e) {
        termLog('error', `Compile error: ${e.message}`);
        setStatus('Error');
    }
}

// ── Syntax Highlighting ────────────────────────────────────────
const NL_KEYWORDS = new Set(['let','show','check','other','repeat','while','task','give','input','and','or','not','true','false']);

function highlightNoveLang(code) {
    const lines = code.split('\n');
    return lines.map(line => {
        if (!line.trim()) return '';
        // Comments
        if (line.trim().startsWith('//')) {
            return `<span class="cm">${escHtml(line)}</span>`;
        }
        // Tokenize for highlighting
        let result = '';
        let i = 0;
        while (i < line.length) {
            // Whitespace
            if (line[i] === ' ' || line[i] === '\t') {
                result += line[i]; i++; continue;
            }
            // Strings
            if (line[i] === '"' || line[i] === "'") {
                const q = line[i]; let j = i + 1;
                while (j < line.length && line[j] !== q) j++;
                result += `<span class="str">${escHtml(line.slice(i, j + 1))}</span>`;
                i = j + 1; continue;
            }
            // Numbers
            if (/\d/.test(line[i])) {
                let j = i;
                while (j < line.length && /[\d.]/.test(line[j])) j++;
                result += `<span class="num">${escHtml(line.slice(i, j))}</span>`;
                i = j; continue;
            }
            // Operators & braces
            if ('+-*/%><=!'.includes(line[i])) {
                let op = line[i];
                if (i + 1 < line.length && '>=!'.includes(line[i]) && line[i + 1] === '=') {
                    op += line[i + 1]; i++;
                }
                if (op === '-' && i + 1 < line.length && line[i + 1] === '>') {
                    op = '->'; i++;
                }
                result += `<span class="op">${escHtml(op)}</span>`;
                i++; continue;
            }
            if ('(){}'.includes(line[i])) {
                result += `<span class="br">${escHtml(line[i])}</span>`;
                i++; continue;
            }
            if (line[i] === ';') {
                result += `<span class="semi">;</span>`;
                i++; continue;
            }
            if (':,'.includes(line[i])) {
                result += `<span class="op">${escHtml(line[i])}</span>`;
                i++; continue;
            }
            // Identifiers / keywords
            if (/[a-zA-Z_]/.test(line[i])) {
                let j = i;
                while (j < line.length && /[a-zA-Z0-9_]/.test(line[j])) j++;
                const word = line.slice(i, j);
                if (NL_KEYWORDS.has(word.toLowerCase())) {
                    result += `<span class="kw">${escHtml(word)}</span>`;
                } else {
                    result += `<span class="id">${escHtml(word)}</span>`;
                }
                i = j; continue;
            }
            result += escHtml(line[i]); i++;
        }
        return result;
    }).join('\n');
}

function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── NLP Analysis Rendering ─────────────────────────────────────
function renderNLPAnalysis(analyses) {
    const container = $('nlp-tab');
    if (!analyses || analyses.length === 0) {
        container.innerHTML = '<div class="empty-state">No NLP analysis data</div>';
        return;
    }
    let html = '';
    analyses.forEach((a, idx) => {
        html += `<div class="nlp-card">
            <div class="nlp-card-header">
                <span class="intent-badge ${a.intent}">${a.intent.replace(/_/g, ' ')}</span>
                <div class="confidence-bar">
                    <div class="bar-bg"><div class="bar-fill" style="width:${a.confidence * 100}%"></div></div>
                    <span class="bar-text">${Math.round(a.confidence * 100)}%</span>
                </div>
            </div>
            <div class="original">"${escHtml(a.original)}"</div>
            <div class="nlp-label">POS Tags</div>
            <div class="pos-tags">
                ${a.pos_tags.map(([word, tag]) =>
                    `<div class="pos-tag"><span class="word">${escHtml(word)}</span><span class="tag">${tag}</span></div>`
                ).join('')}
            </div>
            <div class="nlp-label" style="margin-top:10px">Entities</div>
            <div class="nlp-value">${Object.keys(a.entities).length > 0
                ? Object.entries(a.entities).map(([k,v]) => `<span style="color:var(--accent-cyan)">${k}</span>: <span style="color:var(--accent-amber)">${escHtml(String(v))}</span>`).join(' &nbsp;|&nbsp; ')
                : '<span style="color:var(--text-dim)">none</span>'
            }</div>
            <div class="generated-code">→ ${escHtml(a.generated)}</div>
        </div>`;
    });
    container.innerHTML = html;
}

// ── Token Stream Rendering (Grouped by Category) ──────────────
function renderTokens(tokens) {
    const container = $('tokens-tab');
    if (!tokens || tokens.length === 0) {
        container.innerHTML = '<div class="empty-state">No tokens</div>';
        return;
    }
    const filtered = tokens.filter(t => t.type !== 'EOF');

    // Define categories
    const KEYWORD_TYPES = new Set(['LET','SHOW','CHECK','OTHER','REPEAT','WHILE','TASK','GIVE','INPUT','AND','OR','NOT','TRUE','FALSE']);
    const IDENTIFIER_TYPES = new Set(['IDENTIFIER']);
    const LITERAL_TYPES = new Set(['NUMBER','STRING']);
    const OPERATOR_TYPES = new Set(['PLUS','MINUS','STAR','SLASH','MODULO','EQEQ','NEQ','GEQ','LEQ','GT','LT','EQUALS','ARROW']);
    const SEPARATOR_TYPES = new Set(['SEMI','COMMA','LPAREN','RPAREN','LBRACE','RBRACE','COLON']);
    const SPECIAL_TYPES = new Set(['COMMENT','ERROR']);

    // Collect tokens into groups
    const groups = {
        keywords:    { tokens: [], found: new Set() },
        identifiers: { tokens: [], found: new Set() },
        literals:    { tokens: [], found: new Set() },
        operators:   { tokens: [], found: new Set() },
        separators:  { tokens: [], found: new Set() },
        special:     { tokens: [], found: new Set() },
    };

    filtered.forEach(t => {
        const val = t.type === 'STRING' ? `"${t.value}"` : String(t.value);
        const entry = { val, type: t.type, line: t.line };
        if (KEYWORD_TYPES.has(t.type)) { groups.keywords.tokens.push(entry); groups.keywords.found.add(val); }
        else if (IDENTIFIER_TYPES.has(t.type)) { groups.identifiers.tokens.push(entry); groups.identifiers.found.add(val); }
        else if (LITERAL_TYPES.has(t.type)) { groups.literals.tokens.push(entry); groups.literals.found.add(val); }
        else if (OPERATOR_TYPES.has(t.type)) { groups.operators.tokens.push(entry); groups.operators.found.add(val); }
        else if (SEPARATOR_TYPES.has(t.type)) { groups.separators.tokens.push(entry); groups.separators.found.add(val); }
        else { groups.special.tokens.push(entry); groups.special.found.add(val); }
    });

    // Friendly type names
    const TYPE_NAMES = {
        LET:'Keyword', SHOW:'Keyword', CHECK:'Keyword', OTHER:'Keyword', REPEAT:'Keyword',
        WHILE:'Keyword', TASK:'Keyword', GIVE:'Keyword', INPUT:'Keyword',
        AND:'Logical Keyword', OR:'Logical Keyword', NOT:'Logical Keyword',
        TRUE:'Boolean Keyword', FALSE:'Boolean Keyword',
        IDENTIFIER:'Identifier',
        NUMBER:'Number Literal', STRING:'String Literal',
        PLUS:'Arithmetic (+)', MINUS:'Arithmetic (-)', STAR:'Arithmetic (*)',
        SLASH:'Arithmetic (/)', MODULO:'Arithmetic (%)',
        GT:'Relational (>)', LT:'Relational (<)', GEQ:'Relational (>=)',
        LEQ:'Relational (<=)', EQEQ:'Relational (==)', NEQ:'Relational (!=)',
        EQUALS:'Assignment (=)', ARROW:'Range (->)',
        SEMI:'Semicolon', COMMA:'Comma', LPAREN:'Left Paren',
        RPAREN:'Right Paren', LBRACE:'Left Brace', RBRACE:'Right Brace', COLON:'Colon',
        COMMENT:'Comment', ERROR:'Error',
    };

    let html = `<div class="tok-summary">Total tokens found: <strong>${filtered.length}</strong></div>`;

    // Category definitions
    const categories = [
        {
            key: 'keywords', icon: '1️⃣', title: 'Keywords',
            desc: 'Reserved words with predefined meaning in NoveLang',
            hint: '💡 You cannot use these as variable names',
            color: 'var(--accent-purple)',
        },
        {
            key: 'identifiers', icon: '2️⃣', title: 'Identifiers',
            desc: 'Names given to variables, functions, and parameters',
            hint: '💡 Rules: Cannot start with a number, cannot be a keyword',
            color: 'var(--accent-cyan)',
        },
        {
            key: 'literals', icon: '3️⃣', title: 'Constants (Literals)',
            desc: 'Fixed values used in the program',
            hint: '💡 Types: Number → 10, 3.14 | String → "Hello"',
            color: 'var(--accent-amber)',
        },
        {
            key: 'operators', icon: '4️⃣', title: 'Operators',
            desc: 'Symbols that perform arithmetic, comparison, or logic operations',
            hint: '💡 Arithmetic: +, -, *, / | Relational: >, <, == | Assignment: =',
            color: 'var(--accent-pink)',
        },
        {
            key: 'separators', icon: '5️⃣', title: 'Separators (Delimiters)',
            desc: 'Used to separate and structure code elements',
            hint: '💡 ; (end statement) | ( ) (grouping) | { } (blocks) | , (comma)',
            color: 'var(--accent-green)',
        },
        {
            key: 'special', icon: '6️⃣', title: 'Special Symbols',
            desc: 'Comments and other special tokens',
            hint: '💡 // (single-line comment)',
            color: 'var(--text-secondary)',
        },
    ];

    categories.forEach(cat => {
        const grp = groups[cat.key];
        if (grp.tokens.length === 0) return; // skip empty categories

        html += `<div class="tok-category" style="--cat-color: ${cat.color}">
            <div class="tok-cat-header">
                <span class="tok-cat-icon">${cat.icon}</span>
                <div class="tok-cat-info">
                    <div class="tok-cat-title">${cat.title} <span class="tok-cat-count">(${grp.tokens.length} found)</span></div>
                    <div class="tok-cat-desc">👉 ${cat.desc}</div>
                </div>
            </div>
            <div class="tok-cat-chips">`;

        // Show unique tokens as chips
        const seen = new Set();
        grp.tokens.forEach(t => {
            const uniqueKey = t.val + '|' + t.type;
            const isDuplicate = seen.has(uniqueKey);
            seen.add(uniqueKey);
            html += `<div class="token-chip${isDuplicate ? ' duplicate' : ''}" style="--cat-color: ${cat.color}">
                <span class="tok-val">${escHtml(t.val)}</span>
                <span class="tok-type">${TYPE_NAMES[t.type] || t.type}</span>
            </div>`;
        });

        html += `</div>
            <div class="tok-cat-hint">${cat.hint}</div>
        </div>`;
    });

    container.innerHTML = html;
}

// ── AST Tree Diagram Rendering ─────────────────────────────────
function renderAST(astDict) {
    const container = $('ast-tab');
    if (!astDict) {
        container.innerHTML = '<div class="empty-state">No AST data</div>';
        return;
    }
    const html = '<div class="tree-container"><div class="tree"><ul>' + renderASTTreeNode(astDict) + '</ul></div></div>';
    container.innerHTML = html;
    initDraggableAST(); // Re-init dragging
}

function renderASTTreeNode(node) {
    if (!node || typeof node !== 'object') return '';

    // Build node label
    let nodeType = node.type || 'Node';
    let nodeValue = '';
    if (node.name) nodeValue = node.name;
    else if (node.value !== undefined) nodeValue = String(node.value);
    if (node.op) nodeValue = node.op;
    if (node.callee) nodeValue = node.callee;

    let html = '<li>';
    html += `<div class="tree-node">`;
    html += `<div class="node-type">${escHtml(nodeType)}</div>`;
    if (nodeValue) html += `<div class="node-value">${escHtml(nodeValue)}</div>`;
    if (node.params && node.params.length) html += `<div class="node-value">(${node.params.join(', ')})</div>`;
    html += '</div>';

    if (node.children && node.children.length > 0) {
        html += '<ul>';
        node.children.forEach(child => {
            html += renderASTTreeNode(child);
        });
        html += '</ul>';
    }

    html += '</li>';
    return html;
}

// ── Semantic Analysis Rendering ────────────────────────────────
function renderSemantic(data) {
    const container = $('semantic-tab');
    if (!data) {
        container.innerHTML = '<div class="empty-state">No semantic data</div>';
        return;
    }
    let html = '';

    // Explanation of what Semantic Analysis does
    html += `<div class="sem-explainer">
        <div class="sem-explainer-title">🔍 What is Semantic Analysis?</div>
        <div class="sem-explainer-desc">The semantic analyzer checks your code for <strong>logical correctness</strong> after parsing. It verifies that the program makes sense before execution:</div>
        <ul class="sem-check-list">
            <li><span class="check-icon">✓</span> <strong>Scope Analysis</strong> — Checks if variables are declared before they are used</li>
            <li><span class="check-icon">✓</span> <strong>Type Inference</strong> — Automatically detects the data type of each variable (number, string, boolean)</li>
            <li><span class="check-icon">✓</span> <strong>Function Validation</strong> — Ensures functions are defined before they are called</li>
            <li><span class="check-icon">✓</span> <strong>Symbol Table</strong> — Builds a registry of all variables and functions in the program</li>
        </ul>
    </div>`;

    // Validation Result Summary
    const totalIssues = data.errors.length + data.warnings.length;
    html += `<div class="sem-section"><div class="sem-section-title">📊 Validation Result: ${totalIssues === 0 ? '✅ All Checks Passed' : '⚠ Issues Found'}</div></div>`;

    // Errors
    if (data.errors.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">❌ Errors (Must Fix)</div>';
        data.errors.forEach(e => { html += `<div class="sem-item error"><span class="icon">⚠</span>${escHtml(e)}</div>`; });
        html += '</div>';
    }

    // Warnings
    if (data.warnings.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">⚠ Warnings (Should Review)</div>';
        data.warnings.forEach(w => { html += `<div class="sem-item warning"><span class="icon">⚡</span>${escHtml(w)}</div>`; });
        html += '</div>';
    }

    // Info - Type Inference & Scope Results
    if (data.info.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">💡 Type Inference & Scope Analysis Results</div>';
        data.info.forEach(i => { html += `<div class="sem-item info"><span class="icon">→</span>${escHtml(i)}</div>`; });
        html += '</div>';
    }

    // Symbol Table
    if (data.symbols.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">📋 Symbol Table (All Declared Identifiers)</div>';
        html += '<div class="symbol-table-wrapper"><table class="symbol-table"><thead><tr><th>Name</th><th>Kind</th><th>Inferred Type</th><th>Scope Depth</th></tr></thead><tbody>';
        data.symbols.forEach(s => {
            const kindEmoji = s.kind === 'variable' ? '📦' : s.kind === 'function' ? '⚙️' : '📥';
            html += `<tr>
                <td style="color:var(--accent-cyan)">${kindEmoji} ${escHtml(s.name)}</td>
                <td>${escHtml(s.kind)}</td>
                <td style="color:var(--accent-amber)">${escHtml(s.inferred_type)}</td>
                <td>${s.scope_depth === 0 ? 'Global' : 'Local (depth ' + s.scope_depth + ')'}</td>
            </tr>`;
        });
        html += '</tbody></table></div></div>';
    }

    container.innerHTML = html;
}

// ── API Calls ──────────────────────────────────────────────────
function setStatus(text) { statusText.textContent = text; }

async function doTranslate() {
    const english = englishInput.value.trim();
    if (!english) { termLog('error', 'Please enter some English text first'); return null; }

    resetPipeline();
    setStageActive('nlp');
    setStatus('Translating...');
    termLog('info', 'Starting NLP translation...');

    try {
        const res = await fetch(API + '/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ english }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Translation failed');

        setStageSuccess('nlp', data.time_ms);
        novelangOutput.innerHTML = highlightNoveLang(data.novelang);
        renderNLPAnalysis(data.nlp_analysis);
        termLog('success', `NLP translation complete (${data.time_ms}ms)`);
        setStatus('Translation complete');
        return data.novelang;
    } catch (e) {
        setStageError('nlp');
        termLog('error', `Translation error: ${e.message}`);
        setStatus('Error');
        return null;
    }
}

async function doCompile(code) {
    if (!code) {
        code = novelangOutput.textContent;
        if (!code || code.includes('will appear here')) {
            termLog('error', 'No NoveLang code to compile. Translate first!');
            return;
        }
    }

    setStatus('Compiling...');
    termLog('info', 'Starting compilation pipeline...');

    const stageNames = ['Lexer', 'Parser', 'Semantic', 'Interpreter'];
    const stageKeys  = ['lexer', 'parser', 'semantic', 'interpreter'];

    try {
        const res = await fetch(API + '/api/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
        });
        const data = await res.json();

        // Animate stages
        for (let i = 0; i < data.stages.length; i++) {
            const stage = data.stages[i];
            const key = stageKeys[i];
            setStageActive(key);
            await sleep(200);

            if (stage.status === 'error') {
                setStageError(key);
                termLog('error', `${stage.name}: ${stage.error}`);
                break;
            }

            setStageSuccess(key, stage.time_ms);
            termLog('info', `${stage.name}: ${stage.summary}`);

            // Populate analysis tabs
            if (stage.name === 'Lexer') renderTokens(stage.data);
            if (stage.name === 'Parser') renderAST(stage.data);
            if (stage.name === 'Semantic') renderSemantic(stage.data);
            if (stage.name === 'Interpreter' && stage.data) {
                const result = stage.data;
                const output = result.output || [];
            }
        }

        totalTimeEl.textContent = `Total: ${data.total_time_ms}ms`;
        setStatus(data.success ? 'Compilation successful' : 'Compilation failed');

    } catch (e) {
        termLog('error', `Compile error: ${e.message}`);
        setStatus('Error');
    }
}

async function doRunAll() {
    const english = englishInput.value.trim();
    if (!english) { termLog('error', 'Please enter some English text first'); return; }

    resetPipeline();
    termClear();
    termLog('info', 'Starting full pipeline: English → NoveLang → Execute');
    setStatus('Running full pipeline...');

    try {
        // Step 1: Translate
        setStageActive('nlp');
        const res = await fetch(API + '/api/run-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ english }),
        });
        const data = await res.json();

        // NLP stage
        setStageSuccess('nlp', data.nlp_time_ms);
        termLog('success', `NLP Translation: ${data.nlp_time_ms}ms`);

        // Show NoveLang code
        novelangOutput.innerHTML = highlightNoveLang(data.novelang);
        renderNLPAnalysis(data.nlp_analysis);

        // Compilation stages
        const stageKeys = ['lexer', 'parser', 'semantic', 'interpreter'];
        for (let i = 0; i < (data.stages || []).length; i++) {
            const stage = data.stages[i];
            const key = stageKeys[i];
            setStageActive(key);
            await sleep(250);

            if (stage.status === 'error') {
                setStageError(key);
                termLog('error', `${stage.name}: ${stage.error}`);
                break;
            }

            setStageSuccess(key, stage.time_ms);
            termLog('info', `${stage.name}: ${stage.summary}`);

            if (stage.name === 'Lexer') renderTokens(stage.data);
            if (stage.name === 'Parser') renderAST(stage.data);
            if (stage.name === 'Semantic') renderSemantic(stage.data);
            if (stage.name === 'Interpreter' && stage.data) {
                const result = stage.data;
                const output = result.output || [];
                termLog('success', '────── Program Output ──────');
                output.forEach(line => termLog('output', line));
                termLog('success', '────── End Output ──────');
            }
        }

        totalTimeEl.textContent = `Total: ${data.total_time_ms}ms`;
        setStatus(data.success ? '✓ Pipeline complete' : '✕ Pipeline failed');

    } catch (e) {
        termLog('error', `Pipeline error: ${e.message}`);
        setStatus('Error');
    }
}

// ── Helpers ────────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Event Listeners ────────────────────────────────────────────
btnTranslate.addEventListener('click', doTranslate);
btnCompile.addEventListener('click', () => doCompile());
btnRunAll.addEventListener('click', doRunAll);
btnClear.addEventListener('click', () => {
    termClear();
    resetPipeline();
    totalTimeEl.textContent = '';
    setStatus('Ready');
});

// Keyboard shortcut: Ctrl+Enter to Run All
document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        doRunAll();
    }
});

// ── Draggable AST ──────────────────────────────────────────────
function initDraggableAST() {
    const container = document.querySelector('.tree-container');
    if (!container) return;

    let isDown = false;
    let startX;
    let scrollLeft;
    let startY;
    let scrollTop;

    container.addEventListener('mousedown', (e) => {
        isDown = true;
        container.classList.add('active');
        startX = e.pageX - container.offsetLeft;
        startY = e.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop = container.scrollTop;
    });
    container.addEventListener('mouseleave', () => {
        isDown = false;
        container.classList.remove('active');
    });
    container.addEventListener('mouseup', () => {
        isDown = false;
        container.classList.remove('active');
    });
    container.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const y = e.pageY - container.offsetTop;
        const walkX = (x - startX) * 2;
        const walkY = (y - startY) * 2;
        container.scrollLeft = scrollLeft - walkX;
        container.scrollTop = scrollTop - walkY;
    });
}

// ── Init ───────────────────────────────────────────────────────
loadExampleList();
initDraggableAST();
