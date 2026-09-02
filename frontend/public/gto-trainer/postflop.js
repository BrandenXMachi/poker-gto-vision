// GTO Preflop Trainer - "Postflop Playbook" mode
//
// A third mode alongside Study a Hand and Full Chart. Same wizard feel as
// Study a Hand - answer a few questions, get one answer - but driven by the
// heuristic framework in postflop-lines.js rather than by solved charts.
//
// Two structural decisions worth stating, both of which came out of mapping
// the ten lines onto the funnel:
//
//   - THE ARCHETYPE NAME IS THE REWARD, NOT THE INPUT. The user is never asked
//     "which line are you running" - they answer four plain questions about
//     the spot and the line is named at the end. Ten cards to browse would be
//     a glossary; this is meant to be usable while the framework is still
//     unfamiliar. (The glossary exists too, behind "Browse all ten lines",
//     for once it isn't.)
//
//   - A CELL WITH TWO LINES IS A QUESTION, NOT A CONFLICT. Where several
//     lines match, they differ by what villain did, so the funnel asks. That
//     is the whole of the branch screen.
//
// Must load after app.js, study.js and postflop-lines.js: it reassigns
// switchView(), which study.js defines.

(function () {
    'use strict';

    // -----------------------------------------------------------------------
    // Wire the third tab. study.js's switchView is a two-way toggle written
    // when there were exactly two views; rather than edit it, wrap it - the
    // original already clears both of its own views for any unknown name.
    // -----------------------------------------------------------------------

    const tabPostflopBtn = document.getElementById('tab-postflop');
    const viewPostflopEl = document.getElementById('view-postflop');
    if (!tabPostflopBtn || !viewPostflopEl) return;

    const origSwitchView = switchView;
    switchView = function (view) {
        origSwitchView(view);
        viewPostflopEl.classList.toggle('active', view === 'postflop');
        tabPostflopBtn.classList.toggle('active', view === 'postflop');
    };
    tabPostflopBtn.addEventListener('click', () => switchView('postflop'));

    // -----------------------------------------------------------------------
    // Screen stack
    // -----------------------------------------------------------------------

    const SCREENS = ['position', 'role', 'texture', 'madehand', 'flushdraw', 'straightdraw',
        'branch', 'result', 'browse'];
    const screenEls = {};
    for (const key of SCREENS) screenEls[key] = document.getElementById(`pf-screen-${key}`);

    let pfPosition = null;
    let pfRole = null;
    let pfTexture = null;
    let pfMadeHand = null;
    let pfFlushDraw = null;
    let pfStraightDraw = null;
    let pfHistory = [];

    // Set when the funnel is entered via "Continue to Postflop" from Study
    // Mode (see startPostflopFromBridge below). Carries heroPos/villainPos
    // for the range-width modifier and skips straight to the texture
    // screen, since position/role are already known - texture and the hand
    // filters still have to be asked, since they depend on the flop and
    // Hero's exact two cards, which only the user knows.
    let pfBridge = null;
    let pfHand = null;
    let pfPendingRangeModifier = null;

    function showScreen(key, opts = {}) {
        if (!opts.isBack) {
            const current = SCREENS.find((k) => screenEls[k].classList.contains('active'));
            if (current && current !== key) pfHistory.push(current);
        }
        Object.values(screenEls).forEach((el) => el.classList.remove('active'));
        screenEls[key].classList.add('active');
        updateCrumbs();
    }

    function goBack() {
        const prev = pfHistory.pop();
        if (!prev) return;
        // Clear anything chosen after the screen being returned to, so a back
        // step never leaves a stale answer feeding the next resolution.
        if (prev === 'position') {
            pfRole = pfTexture = pfMadeHand = pfFlushDraw = pfStraightDraw = null;
            pfBridge = null;
        } else if (prev === 'role') {
            pfTexture = pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        } else if (prev === 'texture') {
            pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        } else if (prev === 'madehand') {
            pfFlushDraw = pfStraightDraw = null;
        } else if (prev === 'flushdraw') {
            pfStraightDraw = null;
        }
        showScreen(prev, { isBack: true });
    }

    function reset() {
        pfBridge = null;
        pfHand = null;
        pfPosition = pfRole = pfTexture = pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        pfHistory = [];
        showScreen('position', { isBack: true });
    }

    // -----------------------------------------------------------------------
    // Breadcrumb
    // -----------------------------------------------------------------------

    function labelOf(list, id) {
        const found = list.find((x) => x.id === id);
        return found ? found.label : null;
    }

    function updateCrumbs() {
        const crumbs = [
            ['pf-crumb-position', pfPosition ? labelOf(PF_POSITIONS, pfPosition) : null],
            ['pf-crumb-role', pfRole ? labelOf(PF_ROLES, pfRole) : null],
            ['pf-crumb-texture', pfTexture ? labelOf(PF_TEXTURES, pfTexture) : null],
            ['pf-crumb-category', pfMadeHand ? labelOf(PF_MADE_HAND, pfMadeHand) : null]
        ];
        for (const [id, text] of crumbs) {
            const el = document.getElementById(id);
            if (!el) continue;
            el.textContent = text || '';
            el.hidden = !text;
        }
    }

    // -----------------------------------------------------------------------
    // Steps 1-4: the four questions
    // -----------------------------------------------------------------------

    function renderChoices(containerId, items, onPick, extra) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        for (const item of items) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'choice-btn';

            const label = document.createElement('span');
            label.textContent = item.label;
            btn.appendChild(label);

            const sub = document.createElement('span');
            sub.className = 'choice-sub';
            sub.textContent = extra ? extra(item) : item.sub;
            btn.appendChild(sub);

            btn.addEventListener('click', () => onPick(item.id));
            container.appendChild(btn);
        }
    }

    function currentCell() {
        return {
            position: pfPosition,
            role: pfRole,
            texture: pfTexture,
            category: pfMadeHand ? deriveCategory(pfMadeHand, pfFlushDraw, pfStraightDraw) : null,
            heroPos: pfBridge ? pfBridge.heroPos : null,
            villainPos: pfBridge ? pfBridge.villainPos : null
        };
    }

    /** Resolves the current cell and either shows the result, the branch
     *  screen (several lines match), or the DEFAULT fallback. Shared by the
     *  end of both the manual funnel and the bridged one. */
    function resolveAndShow() {
        const { lines, fallback, rangeModifier } = pfResolve(currentCell());
        pfPendingRangeModifier = rangeModifier;

        if (fallback) {
            showResult(fallback, { isDefault: true });
            return;
        }
        if (lines.length === 1) {
            // One line applies - asking "which of these happened?" with a
            // single answer would be a question with no information in it.
            showResult(lines[0], { isDefault: false });
            return;
        }
        renderBranch(lines);
        showScreen('branch');
    }

    /**
     * Called from Study Mode's "Continue to Postflop" button. `bridge` is a
     * buildBridgeContext() result; `hand` is the Study Mode hand string.
     * Skips position/role entirely - those are derived - and lands on the
     * texture screen, since texture and the hand filters still depend on
     * the flop and Hero's exact two cards, which only the user knows.
     */
    function startPostflopFromBridge(bridge, hand) {
        pfBridge = bridge;
        pfHand = hand;
        pfPosition = bridge.position;
        pfRole = bridge.role;
        pfTexture = pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        pfHistory = [];

        switchView('postflop');
        showScreen('texture', { isBack: true });
    }
    window.startPostflopFromBridge = startPostflopFromBridge;

    function pickPosition(id) {
        pfPosition = id;
        pfRole = pfTexture = pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        pfBridge = null;
        pfHand = null;
        showScreen('role');
    }

    function pickRole(id) {
        pfRole = id;
        pfTexture = pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        showScreen('texture');
    }

    function pickTexture(id) {
        pfTexture = id;
        pfMadeHand = pfFlushDraw = pfStraightDraw = null;
        showScreen('madehand');
    }

    function pickMadeHand(id) {
        pfMadeHand = id;
        pfFlushDraw = pfStraightDraw = null;
        showScreen('flushdraw');
    }

    function pickFlushDraw(id) {
        pfFlushDraw = id;
        pfStraightDraw = null;
        showScreen('straightdraw');
    }

    function pickStraightDraw(id) {
        pfStraightDraw = id;
        resolveAndShow();
    }

    // -----------------------------------------------------------------------
    // Step 5: which line, when several match the same cell
    // -----------------------------------------------------------------------

    function renderBranch(lines) {
        const container = document.getElementById('pf-branch-buttons');
        container.innerHTML = '';
        for (const line of lines) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'choice-btn';

            const label = document.createElement('span');
            label.textContent = line.trigger;
            btn.appendChild(label);

            const sub = document.createElement('span');
            sub.className = 'choice-sub';
            sub.textContent = `${line.id} \u2014 ${line.name}`;
            btn.appendChild(sub);

            btn.addEventListener('click', () => showResult(line, { isDefault: false }));
            container.appendChild(btn);
        }
    }

    // -----------------------------------------------------------------------
    // Result: the line as a three-street path
    // -----------------------------------------------------------------------

    function makeEl(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text != null) el.textContent = text;
        return el;
    }

    function showResult(line, { isDefault }) {
        const titleEl = document.getElementById('pf-result-title');
        const badgeEl = document.getElementById('pf-result-badge');
        const ideaEl = document.getElementById('pf-result-idea');
        const streetsEl = document.getElementById('pf-result-streets');
        const notesEl = document.getElementById('pf-result-notes');

        titleEl.textContent = isDefault ? line.name : `${line.id} \u2014 ${line.name}`;

        badgeEl.textContent = isDefault ? 'DEFAULT' : (line.kind === 'value' ? 'VALUE LINE' : 'BLUFF LINE');
        badgeEl.className = 'pf-badge ' + (isDefault
            ? 'pf-badge-default'
            : (line.kind === 'value' ? 'pf-badge-value' : 'pf-badge-bluff'));

        ideaEl.textContent = line.idea;

        // The three streets, as a path rather than a paragraph - the sizing
        // pattern across streets is the actual content of these lines.
        streetsEl.innerHTML = '';
        for (const s of line.streets) {
            const row = makeEl('div', 'pf-street');
            row.appendChild(makeEl('div', 'pf-street-name', s.street));

            const act = makeEl('div', 'pf-street-action');
            act.appendChild(makeEl('span', 'pf-action-verb', s.action));
            if (s.size && s.size !== '\u2014') {
                act.appendChild(makeEl('span', 'pf-action-size', s.size));
            }
            row.appendChild(act);

            row.appendChild(makeEl('div', 'pf-street-why', s.why));
            streetsEl.appendChild(row);
        }

        // Notes stack: the default disclaimer, the high-risk flag, how the
        // line fails, the named mistakes for this spot, and the standing
        // scope limit. Ordered most-specific first.
        notesEl.innerHTML = '';

        if (isDefault) {
            notesEl.appendChild(makeEl('p', 'result-tree-note pf-note-default', PF_DEFAULT_DISCLAIMER));
        }
        if (pfPendingRangeModifier) {
            notesEl.appendChild(makeEl('p', 'result-tree-note pf-note-range',
                pfPendingRangeModifier.note));
        }
        if (line.risk === 'high') {
            notesEl.appendChild(makeEl('p', 'result-tree-note pf-note-risk',
                'HIGH RISK - this line depends more on a read than any other here.'));
        }
        if (line.failsWhen) {
            notesEl.appendChild(makeEl('p', 'result-tree-note', 'How it fails: ' + line.failsWhen));
        }
        for (const m of pfMistakesFor(currentCell())) {
            notesEl.appendChild(makeEl('p', 'result-tree-note pf-note-mistake',
                `${m.name}: ${m.text}`));
        }
        notesEl.appendChild(makeEl('p', 'result-tree-note', PF_SCOPE_NOTE));

        showScreen('result');
    }

    // -----------------------------------------------------------------------
    // Browse: all ten lines, for when the framework is familiar
    // -----------------------------------------------------------------------

    function describeMatch(line) {
        const pos = line.match.position.length === 2 ? 'IP or OOP' : line.match.position[0];
        const role = line.match.role[0] === 'aggressor' ? 'you raised preflop' : 'you called preflop';
        const tex = line.match.texture.length === PF_TEXTURES.length
            ? 'any board'
            : line.match.texture.map((t) => labelOf(PF_TEXTURES, t)).join(' / ');
        const cats = 'Cat ' + line.match.category.join('/');
        return `${pos} \u00b7 ${role} \u00b7 ${tex} \u00b7 ${cats}`;
    }

    function renderBrowse() {
        const container = document.getElementById('pf-browse-list');
        container.innerHTML = '';
        for (const kind of ['value', 'bluff']) {
            container.appendChild(makeEl('h3', 'pf-browse-heading',
                kind === 'value' ? 'Value lines' : 'Bluff lines'));

            for (const line of POSTFLOP_LINES.filter((l) => l.kind === kind)) {
                const card = makeEl('div', 'pf-browse-card');

                const head = makeEl('div', 'pf-browse-head');
                head.appendChild(makeEl('span', 'pf-browse-id', line.id));
                head.appendChild(makeEl('span', 'pf-browse-name', line.name));
                if (line.risk === 'high') {
                    head.appendChild(makeEl('span', 'pf-badge pf-badge-risk', 'HIGH RISK'));
                }
                card.appendChild(head);

                card.appendChild(makeEl('div', 'pf-browse-match', describeMatch(line)));

                const path = line.streets
                    .map((s) => `${s.action}${s.size && s.size !== '\u2014' ? ' ' + s.size : ''}`)
                    .join('  \u2192  ');
                card.appendChild(makeEl('div', 'pf-browse-path', path));

                container.appendChild(card);
            }
        }
    }

    // -----------------------------------------------------------------------
    // Init
    // -----------------------------------------------------------------------

    renderChoices('pf-position-buttons', PF_POSITIONS, pickPosition);
    renderChoices('pf-role-buttons', PF_ROLES, pickRole);
    renderChoices('pf-texture-buttons', PF_TEXTURES, pickTexture,
        (t) => `${t.example}   -   ${t.sub}`);
    renderChoices('pf-madehand-buttons', PF_MADE_HAND, pickMadeHand);
    renderChoices('pf-flushdraw-buttons', PF_FLUSH_DRAW, pickFlushDraw);
    renderChoices('pf-straightdraw-buttons', PF_STRAIGHT_DRAW, pickStraightDraw);
    renderBrowse();

    const provNote = document.getElementById('pf-provenance-note');
    if (provNote) provNote.textContent = PF_PROVENANCE_NOTE;

    document.querySelectorAll('#view-postflop [data-pf-back]').forEach((btn) => {
        btn.addEventListener('click', goBack);
    });
    document.getElementById('pf-restart-btn').addEventListener('click', reset);
    document.getElementById('pf-browse-btn').addEventListener('click', () => showScreen('browse'));
})();
