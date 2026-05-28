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
const optDot         = $('opt-dot');

// ── Optimizer Cache & State ─────────────────────────────────────
let activeCodeTab        = 'source';
let cachedSourceCode     = '';
let cachedOptimizedCode  = '';
let cachedOptimizedData  = null;  // Full response including stats

// ── Analysis Panel Tab Switching ───────────────────────────────
// Generic handler for [data-tab] buttons (Analysis panel tabs only)
document.querySelectorAll('.tab[data-tab]').forEach(tab => {
    tab.addEventListener('click', () => {
        const panel = tab.closest('.panel');
        panel.querySelectorAll('.tab[data-tab]').forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
        });
        panel.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        const target = $(tab.getAttribute('data-tab'));
        if (target) target.classList.add('active');
    });
});

// ── Code Tab Switching (Source / Optimized) ─────────────────────
// These use [data-code-tab] to avoid conflicting with the analysis tabs
document.querySelectorAll('[data-code-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
        switchCodeTab(btn.getAttribute('data-code-tab'));
    });
});

async function switchCodeTab(tabName) {
    activeCodeTab = tabName;

    // Update tab active state
    document.querySelectorAll('[data-code-tab]').forEach(btn => {
        const isActive = btn.getAttribute('data-code-tab') === tabName;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', String(isActive));
    });

    if (tabName === 'source') {
        if (cachedSourceCode) {
            novelangOutput.innerHTML = highlightNoveLang(cachedSourceCode);
        } else {
            novelangOutput.innerHTML = '<span class="placeholder">NoveLang code will appear here after translation...</span>';
        }
    } else if (tabName === 'optimizer') {
        if (!cachedSourceCode) {
            novelangOutput.innerHTML = '<span class="placeholder">Translate English to NoveLang first, then click Optimized...</span>';
            return;
        }

        if (cachedOptimizedCode) {
            // Already have cached result — just show it
            novelangOutput.innerHTML = highlightNoveLang(cachedOptimizedCode);
            // Ensure analysis tab is updated too
            if (cachedOptimizedData) renderOptimizerAnalysis(cachedOptimizedData);
            return;
        }

        // Run optimization
        novelangOutput.innerHTML = '<span class="placeholder optimizer-loading">Running optimizer...</span>';
        setStatus('Optimizing...');
        try {
            const res = await fetch(API + '/api/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: cachedSourceCode }),
            });
            const data = await res.json();

            if (!data.success) throw new Error(data.error || 'Optimization failed');

            cachedOptimizedCode = data.optimized_code;
            cachedOptimizedData = data;
            novelangOutput.innerHTML = highlightNoveLang(cachedOptimizedCode);

            // Update optimizer analysis tab
            renderOptimizerAnalysis(data);

            // Glow the opt-dot to show optimization ran
            if (optDot) optDot.classList.add('active');

            const saved = data.stats ? data.stats.lines_removed : 0;
            termLog('success', `Optimizer: ${data.time_ms}ms | ${saved} line(s) simplified/eliminated`);
            setStatus(`Optimization complete — ${saved} optimization(s) applied`);

        } catch (e) {
            termLog('error', `Optimizer error: ${e.message}`);
            setStatus('Optimization error');
            novelangOutput.innerHTML = `<span style="color:var(--accent-red)">Optimizer Error: ${escHtml(e.message)}</span>`;
        }
    }
}

// ── Load Examples ──────────────────────────────────────────────
async function loadExampleList() {
    try {
        const res = await fetch(API + '/api/examples');
        const examples = await res.json();
        examples.forEach(ex => {
            const opt = document.createElement('option');
            opt.value = ex.id;
            opt.textContent = ex.name;
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
            resetAll();
            termLog('info', `Loaded example: ${data.name}`);
        }
    } catch (e) {
        termLog('error', 'Failed to load example');
    }
});

// ── Pipeline Visualization ─────────────────────────────────────
const stageMap  = { nlp: 0, lexer: 1, parser: 2, semantic: 3, interpreter: 4 };
const stageEls  = document.querySelectorAll('.pipeline-stage');
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

// ── Reset Everything ───────────────────────────────────────────
function resetAll() {
    resetPipeline();
    termClear();
    cachedSourceCode    = '';
    cachedOptimizedCode = '';
    cachedOptimizedData = null;
    if (optDot) optDot.classList.remove('active');
    totalTimeEl.textContent = '';
    switchCodeTab('source');
    // Clear analysis tabs
    $('nlp-tab').innerHTML       = '<div class="empty-state">Run the translator to see NLP analysis</div>';
    $('tokens-tab').innerHTML    = '<div class="empty-state">Compile code to see token stream</div>';
    $('ast-tab').innerHTML       = '<div class="empty-state">Compile code to see the AST</div>';
    $('semantic-tab').innerHTML  = '<div class="empty-state">Run the compiler to see semantic analysis</div>';
    $('optimizer-tab').innerHTML = '<div class="empty-state">Click "Optimized" tab in NoveLang Code panel to run optimizer</div>';
    setStatus('Ready');
}

// ── Step-by-Step Pipeline (click pipeline stage) ──────────────
const TARGET_STAGES = ['lexer', 'parser', 'semantic', 'interpreter'];
stageEls.forEach(el => {
    el.addEventListener('click', async () => {
        const stage = el.getAttribute('data-stage');
        if (stage === 'nlp') {
            await doTranslate();
        } else {
            const targetIdx = TARGET_STAGES.indexOf(stage);
            if (targetIdx !== -1) await doCompileUpTo(targetIdx);
        }
    });
});

async function doCompileUpTo(targetIdx) {
    const code = getActiveCode();
    if (!code) { termLog('error', 'No NoveLang code to compile. Translate first!'); return; }

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
        for (let i = 0; i < connectorEls.length; i++) connectorEls[i].classList.remove('active');

        const stageKeys = ['lexer', 'parser', 'semantic', 'interpreter'];
        for (let i = 0; i <= targetIdx && i < (data.stages || []).length; i++) {
            const stage = data.stages[i];
            const key   = stageKeys[i];
            setStageActive(key);
            await sleep(200);

            if (stage.status === 'error') {
                setStageError(key);
                termLog('error', `${stage.name}: ${stage.error}`);
                break;
            }
            setStageSuccess(key, stage.time_ms);
            termLog('info', `${stage.name}: ${stage.summary}`);

            if (stage.name === 'Lexer') { renderTokens(stage.data); switchAnalysisTab('tokens-tab'); }
            if (stage.name === 'Parser') { renderAST(stage.data); switchAnalysisTab('ast-tab'); }
            if (stage.name === 'Semantic') { renderSemantic(stage.data); switchAnalysisTab('semantic-tab'); }
        }
        setStatus(data.success ? '✓ Step complete' : '✕ Step failed');
    } catch (e) {
        termLog('error', `Compile error: ${e.message}`);
        setStatus('Error');
    }
}

// Switch analysis panel tab programmatically
function switchAnalysisTab(tabId) {
    const btn = document.querySelector(`[data-tab="${tabId}"]`);
    if (btn) btn.click();
}

// ── Get Code From Active Tab ───────────────────────────────────
function getActiveCode() {
    if (activeCodeTab === 'optimizer' && cachedOptimizedCode) return cachedOptimizedCode;
    if (cachedSourceCode) return cachedSourceCode;
    // Fall back to DOM text if we have it
    const raw = novelangOutput.textContent;
    if (raw && !raw.includes('will appear here') && !raw.includes('Translate')) return raw;
    return null;
}

// ── Syntax Highlighting ────────────────────────────────────────
const NL_KEYWORDS = new Set([
    'let','show','check','other','repeat','while','task','give','input','and','or','not','true','false'
]);

function highlightNoveLang(code) {
    const lines = code.split('\n');
    return lines.map(line => {
        if (!line.trim()) return '';
        if (line.trim().startsWith('//')) {
            return `<span class="cm">${escHtml(line)}</span>`;
        }
        let result = '';
        let i = 0;
        while (i < line.length) {
            if (line[i] === ' ' || line[i] === '\t') { result += line[i]; i++; continue; }
            if (line[i] === '"' || line[i] === "'") {
                const q = line[i]; let j = i + 1;
                while (j < line.length && line[j] !== q) j++;
                result += `<span class="str">${escHtml(line.slice(i, j + 1))}</span>`;
                i = j + 1; continue;
            }
            if (/\d/.test(line[i])) {
                let j = i;
                while (j < line.length && /[\d.]/.test(line[j])) j++;
                result += `<span class="num">${escHtml(line.slice(i, j))}</span>`;
                i = j; continue;
            }
            if ('+-*/%><!='.includes(line[i])) {
                let op = line[i];
                if (i + 1 < line.length && '>=!'.includes(line[i]) && line[i + 1] === '=') { op += line[i + 1]; i++; }
                if (op === '-' && i + 1 < line.length && line[i + 1] === '>') { op = '->'; i++; }
                result += `<span class="op">${escHtml(op)}</span>`;
                i++; continue;
            }
            if ('(){}'.includes(line[i])) { result += `<span class="br">${escHtml(line[i])}</span>`; i++; continue; }
            if (line[i] === ';') { result += `<span class="semi">;</span>`; i++; continue; }
            if (':,'.includes(line[i])) { result += `<span class="op">${escHtml(line[i])}</span>`; i++; continue; }
            if (/[a-zA-Z_]/.test(line[i])) {
                let j = i;
                while (j < line.length && /[a-zA-Z0-9_]/.test(line[j])) j++;
                const word = line.slice(i, j);
                result += NL_KEYWORDS.has(word.toLowerCase())
                    ? `<span class="kw">${escHtml(word)}</span>`
                    : `<span class="id">${escHtml(word)}</span>`;
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
    analyses.forEach((a) => {
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
                ? Object.entries(a.entities).map(([k,v]) =>
                    `<span style="color:var(--accent-cyan)">${k}</span>: <span style="color:var(--accent-amber)">${escHtml(String(v))}</span>`
                  ).join(' &nbsp;|&nbsp; ')
                : '<span style="color:var(--text-dim)">none</span>'
            }</div>
            <div class="generated-code">→ ${escHtml(a.generated)}</div>
        </div>`;
    });
    container.innerHTML = html;
}

// ── Optimizer Analysis Rendering ───────────────────────────────
function renderOptimizerAnalysis(data) {
    const container = $('optimizer-tab');
    if (!data || !data.success) {
        container.innerHTML = '<div class="empty-state">No optimization data available</div>';
        return;
    }

    const stats = data.stats || {};
    const origLines = stats.original_lines || 0;
    const optLines  = stats.optimized_lines || 0;
    const removed   = stats.lines_removed || 0;
    const passes    = stats.passes || [];
    const pct = origLines > 0 ? Math.round((removed / origLines) * 100) : 0;

    let html = `<div class="opt-explainer">
        <div class="opt-explainer-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;flex-shrink:0"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            What is Code Optimization?
        </div>
        <div class="opt-explainer-desc">The optimizer transforms your AST to produce equivalent but <strong>faster and cleaner</strong> NoveLang code without changing its behavior.</div>
        <ul class="opt-pass-list">
            ${passes.map(p => `<li><span class="opt-check">&#10003;</span><strong>${escHtml(p)}</strong></li>`).join('')}
        </ul>
    </div>`;

    // Stats cards
    html += `<div class="opt-stats-grid">
        <div class="opt-stat-card">
            <div class="opt-stat-val">${origLines}</div>
            <div class="opt-stat-label">Original Lines</div>
        </div>
        <div class="opt-stat-card opt-stat-accent">
            <div class="opt-stat-val">${optLines}</div>
            <div class="opt-stat-label">Optimized Lines</div>
        </div>
        <div class="opt-stat-card opt-stat-green">
            <div class="opt-stat-val">${removed}</div>
            <div class="opt-stat-label">Lines Simplified</div>
        </div>
        <div class="opt-stat-card">
            <div class="opt-stat-val">${pct}%</div>
            <div class="opt-stat-label">Reduction</div>
        </div>
    </div>`;

    if (removed === 0) {
        html += `<div class="opt-no-change" style="margin-top: 20px; padding: 16px; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent-green); border-radius: 8px; text-align: center;">
            <div style="color: var(--accent-green); font-weight: 600; font-size: 1.1rem; margin-bottom: 4px;">✅ No Optimization Required</div>
            <div style="color: var(--text-dim); font-size: 0.95rem;">The code is already fully optimal. No redundant operations or dead code found!</div>
        </div>`;
    } else {
        // Side-by-side diff
        html += `<div class="opt-diff-header">
            <div class="opt-diff-label opt-diff-before">Before Optimization</div>
            <div class="opt-diff-label opt-diff-after">After Optimization</div>
        </div>
        <div class="opt-diff-grid">
            <pre class="opt-diff-code opt-before">${highlightNoveLang(data.original_code || '')}</pre>
            <pre class="opt-diff-code opt-after">${highlightNoveLang(data.optimized_code || '')}</pre>
        </div>`;
    }

    // Timing
    html += `<div class="opt-timing">Optimization completed in <strong>${data.time_ms}ms</strong></div>`;

    container.innerHTML = html;

    // Switch analysis panel to the optimizer tab automatically
    switchAnalysisTab('optimizer-tab');
}

// ── Token Stream Rendering ─────────────────────────────────────
function renderTokens(tokens) {
    const container = $('tokens-tab');
    if (!tokens || tokens.length === 0) {
        container.innerHTML = '<div class="empty-state">No tokens</div>';
        return;
    }
    const filtered = tokens.filter(t => t.type !== 'EOF');
    const KEYWORD_TYPES  = new Set(['LET','SHOW','CHECK','OTHER','REPEAT','WHILE','TASK','GIVE','INPUT','AND','OR','NOT','TRUE','FALSE']);
    const IDENTIFIER_TYPES = new Set(['IDENTIFIER']);
    const LITERAL_TYPES  = new Set(['NUMBER','STRING']);
    const OPERATOR_TYPES = new Set(['PLUS','MINUS','STAR','SLASH','MODULO','EQEQ','NEQ','GEQ','LEQ','GT','LT','EQUALS','ARROW']);
    const SEPARATOR_TYPES = new Set(['SEMI','COMMA','LPAREN','RPAREN','LBRACE','RBRACE','COLON']);

    const groups = {
        keywords:    { tokens: [], found: new Set() },
        identifiers: { tokens: [], found: new Set() },
        literals:    { tokens: [], found: new Set() },
        operators:   { tokens: [], found: new Set() },
        separators:  { tokens: [], found: new Set() },
        special:     { tokens: [], found: new Set() },
    };

    filtered.forEach(t => {
        const val   = t.type === 'STRING' ? `"${t.value}"` : String(t.value);
        const entry = { val, type: t.type, line: t.line };
        if      (KEYWORD_TYPES.has(t.type))   { groups.keywords.tokens.push(entry);    groups.keywords.found.add(val); }
        else if (IDENTIFIER_TYPES.has(t.type)){ groups.identifiers.tokens.push(entry); groups.identifiers.found.add(val); }
        else if (LITERAL_TYPES.has(t.type))   { groups.literals.tokens.push(entry);    groups.literals.found.add(val); }
        else if (OPERATOR_TYPES.has(t.type))  { groups.operators.tokens.push(entry);   groups.operators.found.add(val); }
        else if (SEPARATOR_TYPES.has(t.type)) { groups.separators.tokens.push(entry);  groups.separators.found.add(val); }
        else                                   { groups.special.tokens.push(entry);     groups.special.found.add(val); }
    });

    const TYPE_NAMES = {
        LET:'Keyword', SHOW:'Keyword', CHECK:'Keyword', OTHER:'Keyword', REPEAT:'Keyword',
        WHILE:'Keyword', TASK:'Keyword', GIVE:'Keyword', INPUT:'Keyword',
        AND:'Logical Keyword', OR:'Logical Keyword', NOT:'Logical Keyword',
        TRUE:'Boolean Keyword', FALSE:'Boolean Keyword',
        IDENTIFIER:'Identifier', NUMBER:'Number Literal', STRING:'String Literal',
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

    const categories = [
        { key: 'keywords',    icon: '①', title: 'Keywords',               desc: 'Reserved words with predefined meaning in NoveLang', hint: '💡 You cannot use these as variable names', color: 'var(--accent-blue)' },
        { key: 'identifiers', icon: '②', title: 'Identifiers',            desc: 'Names given to variables, functions, and parameters', hint: '💡 Rules: Cannot start with a number, cannot be a keyword', color: 'var(--accent-cyan)' },
        { key: 'literals',    icon: '③', title: 'Constants (Literals)',    desc: 'Fixed values used in the program', hint: '💡 Types: Number → 10, 3.14 | String → "Hello"', color: 'var(--accent-amber)' },
        { key: 'operators',   icon: '④', title: 'Operators',               desc: 'Symbols that perform arithmetic, comparison, or logic', hint: '💡 Arithmetic: +, -, *, / | Relational: >, <, == | Assignment: =', color: 'var(--accent-pink)' },
        { key: 'separators',  icon: '⑤', title: 'Separators (Delimiters)', desc: 'Used to separate and structure code elements', hint: '💡 ; (end statement) | ( ) (grouping) | { } (blocks) | , (comma)', color: 'var(--accent-green)' },
        { key: 'special',     icon: '⑥', title: 'Special Symbols',         desc: 'Comments and other special tokens', hint: '💡 // (single-line comment)', color: 'var(--text-secondary)' },
    ];

    categories.forEach(cat => {
        const grp = groups[cat.key];
        if (grp.tokens.length === 0) return;
        html += `<div class="tok-category" style="--cat-color: ${cat.color}">
            <div class="tok-cat-header">
                <span class="tok-cat-icon">${cat.icon}</span>
                <div class="tok-cat-info">
                    <div class="tok-cat-title">${cat.title} <span class="tok-cat-count">(${grp.tokens.length} found)</span></div>
                    <div class="tok-cat-desc">👉 ${cat.desc}</div>
                </div>
            </div>
            <div class="tok-cat-chips">`;
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
    container.innerHTML = '<div class="tree-container"><div class="tree"><ul>' + renderASTTreeNode(astDict) + '</ul></div></div>';
    initDraggableAST();
}

function renderASTTreeNode(node) {
    if (!node || typeof node !== 'object') return '';
    let nodeType  = node.type || 'Node';
    let nodeValue = '';
    if (node.name) nodeValue = node.name;
    else if (node.value !== undefined) nodeValue = String(node.value);
    if (node.op)     nodeValue = node.op;
    if (node.callee) nodeValue = node.callee;
    let html = '<li>';
    html += `<div class="tree-node"><div class="node-type">${escHtml(nodeType)}</div>`;
    if (nodeValue) html += `<div class="node-value">${escHtml(nodeValue)}</div>`;
    if (node.params && node.params.length) html += `<div class="node-value">(${node.params.join(', ')})</div>`;
    html += '</div>';
    if (node.children && node.children.length > 0) {
        html += '<ul>';
        node.children.forEach(child => { html += renderASTTreeNode(child); });
        html += '</ul>';
    }
    html += '</li>';
    return html;
}

// ── Semantic Analysis Rendering ────────────────────────────────
function renderSemantic(data) {
    const container = $('semantic-tab');
    if (!data) { container.innerHTML = '<div class="empty-state">No semantic data</div>'; return; }
    let html = `<div class="sem-explainer">
        <div class="sem-explainer-title">What is Semantic Analysis?</div>
        <div class="sem-explainer-desc">The semantic analyzer checks your code for <strong>logical correctness</strong> after parsing:</div>
        <ul class="sem-check-list">
            <li><span class="check-icon">✓</span> <strong>Scope Analysis</strong> — Checks if variables are declared before they are used</li>
            <li><span class="check-icon">✓</span> <strong>Type Inference</strong> — Detects data types (number, string, boolean)</li>
            <li><span class="check-icon">✓</span> <strong>Function Validation</strong> — Ensures functions are defined before they are called</li>
            <li><span class="check-icon">✓</span> <strong>Symbol Table</strong> — Builds a registry of all identifiers in the program</li>
        </ul>
    </div>`;
    const totalIssues = data.errors.length + data.warnings.length;
    html += `<div class="sem-section"><div class="sem-section-title">Validation Result: ${totalIssues === 0 ? '✅ All Checks Passed' : '⚠ Issues Found'}</div></div>`;
    if (data.errors.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">❌ Errors (Must Fix)</div>';
        data.errors.forEach(e => { html += `<div class="sem-item error"><span class="icon">⚠</span>${escHtml(e)}</div>`; });
        html += '</div>';
    }
    if (data.warnings.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">⚠ Warnings (Should Review)</div>';
        data.warnings.forEach(w => { html += `<div class="sem-item warning"><span class="icon">⚡</span>${escHtml(w)}</div>`; });
        html += '</div>';
    }
    if (data.info.length > 0) {
        html += '<div class="sem-section"><div class="sem-section-title">💡 Type Inference & Scope Analysis Results</div>';
        data.info.forEach(i => { html += `<div class="sem-item info"><span class="icon">→</span>${escHtml(i)}</div>`; });
        html += '</div>';
    }
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

    // Reset optimizer state
    cachedOptimizedCode = '';
    cachedOptimizedData = null;
    if (optDot) optDot.classList.remove('active');

    try {
        const res = await fetch(API + '/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ english }),
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Translation failed');

        setStageSuccess('nlp', data.time_ms);
        cachedSourceCode = data.novelang;
        await switchCodeTab('source');
        renderNLPAnalysis(data.nlp_analysis);
        termLog('success', `NLP translation complete (${data.time_ms}ms)`);
        setStatus('Translation complete — click Optimized to run optimizer');
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
        code = getActiveCode();
        if (!code) { termLog('error', 'No NoveLang code to compile. Translate first!'); return; }
    }

    setStatus('Compiling...');
    termLog('info', `Compiling ${activeCodeTab === 'optimizer' ? 'optimized' : 'source'} code...`);

    const stageKeys = ['lexer', 'parser', 'semantic', 'interpreter'];

    try {
        const res = await fetch(API + '/api/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
        });
        const data = await res.json();

        for (let i = 0; i < data.stages.length; i++) {
            const stage = data.stages[i];
            const key   = stageKeys[i];
            setStageActive(key);
            await sleep(200);

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
                const output = stage.data.output || [];
                termLog('success', '────── Program Output ──────');
                output.forEach(line => termLog('output', line));
                termLog('success', '────── End Output ──────');
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
    cachedOptimizedCode = '';
    cachedOptimizedData = null;
    if (optDot) optDot.classList.remove('active');

    termLog('info', 'Starting full pipeline: English → NoveLang → Execute');
    setStatus('Running full pipeline...');

    try {
        setStageActive('nlp');
        const res = await fetch(API + '/api/run-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ english }),
        });
        const data = await res.json();

        setStageSuccess('nlp', data.nlp_time_ms);
        termLog('success', `NLP Translation: ${data.nlp_time_ms}ms`);

        cachedSourceCode = data.novelang;
        await switchCodeTab('source');
        renderNLPAnalysis(data.nlp_analysis);

        const stageKeys = ['lexer', 'parser', 'semantic', 'interpreter'];
        for (let i = 0; i < (data.stages || []).length; i++) {
            const stage = data.stages[i];
            const key   = stageKeys[i];
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
                const output = stage.data.output || [];
                termLog('success', '────── Program Output ──────');
                output.forEach(line => termLog('output', line));
                termLog('success', '────── End Output ──────');
            }
        }

        totalTimeEl.textContent = `Total: ${data.total_time_ms}ms`;
        setStatus(data.success ? '✓ Pipeline complete — try Optimized tab!' : '✕ Pipeline failed');

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
btnClear.addEventListener('click', resetAll);

// Keyboard shortcut: Ctrl+Enter to Run All
document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); doRunAll(); }
});

// ── Draggable AST ──────────────────────────────────────────────
function initDraggableAST() {
    const container = document.querySelector('.tree-container');
    if (!container) return;
    let isDown = false, startX, scrollLeft, startY, scrollTop;
    container.addEventListener('mousedown', e => {
        isDown = true;
        container.classList.add('active');
        startX = e.pageX - container.offsetLeft;
        startY = e.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop  = container.scrollTop;
    });
    container.addEventListener('mouseleave', () => { isDown = false; container.classList.remove('active'); });
    container.addEventListener('mouseup',    () => { isDown = false; container.classList.remove('active'); });
    container.addEventListener('mousemove', e => {
        if (!isDown) return;
        e.preventDefault();
        container.scrollLeft = scrollLeft - (e.pageX - container.offsetLeft - startX) * 2;
        container.scrollTop  = scrollTop  - (e.pageY - container.offsetTop  - startY) * 2;
    });
}

// ── Init ───────────────────────────────────────────────────────
loadExampleList();
initDraggableAST();
