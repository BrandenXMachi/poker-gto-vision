// GTO Preflop Trainer - "Study a Hand" mode
//
// A guided, hand-first wizard: pick one hand, then Hero's position, then
// the betting scenario, then Villain's position - with an early "always
// fold" shortcut at each step if the hand is never worth playing given
// what's been selected so far. Reuses constants/helpers already defined
// in app.js (RANKS, POSITIONS, POS_ORDER, loadJSON, parseUPI, buildGrid,
// findChartPath), since both scripts share the same top-level scope.

// ---------------------------------------------------------------------------
// Tab switching (Study a Hand <-> Full Chart)
// ---------------------------------------------------------------------------

const tabStudyBtn = document.getElementById('tab-study');
const tabChartBtn = document.getElementById('tab-chart');
const viewStudyEl = document.getElementById('view-study');
const viewChartEl = document.getElementById('view-chart');

function switchView(view) {
    viewStudyEl.classList.toggle('active', view === 'study');
    viewChartEl.classList.toggle('active', view === 'chart');
    tabStudyBtn.classList.toggle('active', view === 'study');
    tabChartBtn.classList.toggle('active', view === 'chart');
}

tabStudyBtn.addEventListener('click', () => switchView('study'));
tabChartBtn.addEventListener('click', () => switchView('chart'));

// ---------------------------------------------------------------------------
// Scenario metadata
// ---------------------------------------------------------------------------

const SCENARIOS = ['RFI', 'vs_Open', 'vs_3B', 'vs_4B', 'vs_5B'];

const SCENARIO_LABELS = {
    RFI: 'Unopened (Hero Opens)',
    vs_Open: 'Facing an Open',
    vs_3B: 'Facing a 3-Bet',
    vs_4B: 'Facing a 4-Bet',
    vs_5B: 'Facing a 5-Bet (All-In)'
};

const SCENARIO_SUBLABELS = {
    RFI: 'No one has entered the pot yet',
    vs_Open: 'A single raise in front of Hero',
    vs_3B: 'Hero opened, Villain re-raised',
    vs_4B: 'Hero 3-bet, Villain re-raised again',
    vs_5B: 'Hero 4-bet, Villain shoved all-in'
};

// ---------------------------------------------------------------------------
// Hand categorization (for the hand-select grid coloring)
// ---------------------------------------------------------------------------

const RANK_IDX = { A: 0, K: 1, Q: 2, J: 3, T: 4, '9': 5, '8': 6, '7': 7, '6': 8, '5': 9, '4': 10, '3': 11, '2': 12 };
const BROADWAY_SET = new Set(['A', 'K', 'Q', 'J', 'T']);

/**
 * Classify a hand into one visual category for the hand-select grid:
 * pair, suited-ace, suited-broadway, offsuit-broadway, suited-connector,
 * suited-gapper, or other.
 */
function categorizeHand(hand) {
    if (hand.length === 2) return 'pair';
    const r1 = hand[0];
    const r2 = hand[1];
    const suited = hand[2] === 's';

    if (suited && (r1 === 'A' || r2 === 'A')) return 'suited-ace';

    const bothBroadway = BROADWAY_SET.has(r1) && BROADWAY_SET.has(r2);
    if (suited && bothBroadway) return 'suited-broadway';
    if (!suited && bothBroadway) return 'offsuit-broadway';

    if (suited) {
        const gap = Math.abs(RANK_IDX[r1] - RANK_IDX[r2]) - 1;
        if (gap === 0) return 'suited-connector';
        if (gap === 1) return 'suited-gapper';
    }

    return 'other';
}

// ---------------------------------------------------------------------------
// Frequency helpers
// ---------------------------------------------------------------------------

function classifyAction(name) {
    const lower = name.toLowerCase();
    if (lower.includes('fold')) return 'fold';
    if (lower.includes('call')) return 'call';
    return 'raise';
}

/** Aggregate {raise, call, fold} frequencies for one hand from chart data. */
function computeFreqsForHand(chartData, hand) {
    const result = { raise: 0, call: 0, fold: 0 };
    if (!chartData) return result;
    const strategy = chartData.strategy;
    for (const actionObj of strategy.actions) {
        const range = parseUPI(strategy.upi_ranges[actionObj.name]);
        const freq = range[hand] || 0;
        if (!freq) continue;
        result[classifyAction(actionObj.name)] += freq;
    }
    return result;
}

/** Load the chart for a given hero/villain/scenario combo, trying all
 *  candidate filenames. Returns null if no chart exists (illegal combo
 *  or missing file). */
async function loadChartFor(hero, villain, scenario) {
    let paths = findChartPath(hero, villain, scenario);
    if (!paths) return null;
    if (!Array.isArray(paths)) paths = [paths];
    for (const p of paths) {
        const data = await loadJSON(p);
        if (data) return data;
    }
    return null;
}

function isLegalCombo(hero, villain, scenario) {
    return findChartPath(hero, villain, scenario) !== null;
}

function isScenarioLegalForHero(hero, scenario) {
    if (scenario === 'RFI') return findChartPath(hero, null, 'RFI') !== null;
    return POSITIONS.some(v => v !== hero && isLegalCombo(hero, v, scenario));
}

/**
 * Whether a given (hero, villain, scenario) spot is "reachable" with this
 * specific hand - i.e. Hero would actually have taken the earlier raises
 * needed to get here. vs_Open is always reachable (Hero hasn't acted yet).
 * vs_3B/vs_5B require Hero to have opened. vs_4B/vs_5B require Hero to have
 * 3-bet/4-bet this exact matchup already.
 */
async function isReachable(hero, villain, scenario, hand) {
    if (scenario === 'vs_Open') return true;
    if (scenario === 'vs_3B') {
        const f = await getRfiFreqs(hero, hand);
        return f.raise > 0;
    }
    if (scenario === 'vs_4B') {
        const f = await getVsOpenFreqs(hero, villain, hand);
        return f.raise > 0;
    }
    if (scenario === 'vs_5B') {
        const f1 = await getRfiFreqs(hero, hand);
        if (f1.raise <= 0) return false;
        const f2 = await getVs3BFreqs(hero, villain, hand);
        return f2.raise > 0;
    }
    return false;
}

async function getRfiFreqs(hero, hand) {
    const data = await loadChartFor(hero, null, 'RFI');
    return computeFreqsForHand(data, hand);
}

async function getVsOpenFreqs(hero, villain, hand) {
    const data = await loadChartFor(hero, villain, 'vs_Open');
    return computeFreqsForHand(data, hand);
}

async function getVs3BFreqs(hero, villain, hand) {
    const data = await loadChartFor(hero, villain, 'vs_3B');
    return computeFreqsForHand(data, hand);
}

async function getLeafFreqs(hero, villain, scenario, hand) {
    const data = await loadChartFor(hero, villain, scenario);
    return computeFreqsForHand(data, hand);
}

/** Villains that are both legal (position order) and reachable (Hero
 *  would actually have gotten here) for a given hero+scenario+hand. */
async function reachableVillains(hero, scenario, hand) {
    const out = [];
    for (const v of POSITIONS) {
        if (v === hero) continue;
        if (!isLegalCombo(hero, v, scenario)) continue;
        if (await isReachable(hero, v, scenario, hand)) out.push(v);
    }
    return out;
}

// ---------------------------------------------------------------------------
// Step 1 & 2 aggregate "always fold" checks
// ---------------------------------------------------------------------------

/** After Hero's position is fixed: is this hand a guaranteed fold in
 *  every reachable spot Hero could ever be in? */
async function step1AllFold(hero, hand) {
    for (const scenario of SCENARIOS) {
        if (!isScenarioLegalForHero(hero, scenario)) continue;
        if (scenario === 'RFI') {
            const f = await getRfiFreqs(hero, hand);
            if (f.raise > 0 || f.call > 0) return false;
            continue;
        }
        const villains = await reachableVillains(hero, scenario, hand);
        for (const v of villains) {
            const f = await getLeafFreqs(hero, v, scenario, hand);
            if (f.raise > 0 || f.call > 0) return false;
        }
    }
    return true;
}

/** After Hero's position + scenario are fixed: is this hand a guaranteed
 *  fold across every reachable villain in that scenario? Returns
 *  { allFold, villains, unreachable }. */
async function step2AllFold(hero, scenario, hand) {
    if (scenario === 'RFI') {
        const f = await getRfiFreqs(hero, hand);
        return { allFold: f.raise <= 0 && f.call <= 0, villains: [] };
    }
    const villains = await reachableVillains(hero, scenario, hand);
    if (villains.length === 0) return { allFold: true, villains: [], unreachable: true };
    for (const v of villains) {
        const f = await getLeafFreqs(hero, v, scenario, hand);
        if (f.raise > 0 || f.call > 0) return { allFold: false, villains };
    }
    return { allFold: true, villains };
}

// ---------------------------------------------------------------------------
// Wizard state & navigation
// ---------------------------------------------------------------------------

let studyHand = null;
let studyHero = null;
let studyScenario = null;
let studyVillain = null;
let studyLegalScenarios = [];
let screenHistory = [];
let studyBusy = false;

const screenEls = {
    hand: document.getElementById('study-screen-hand'),
    hero: document.getElementById('study-screen-hero'),
    scenario: document.getElementById('study-screen-scenario'),
    villain: document.getElementById('study-screen-villain'),
    result: document.getElementById('study-screen-result')
};

const crumbHandEl = document.getElementById('crumb-hand');
const crumbHeroEl = document.getElementById('crumb-hero');
const crumbScenarioEl = document.getElementById('crumb-scenario');
const crumbVillainEl = document.getElementById('crumb-villain');

function idForScreen(el) {
    return Object.keys(screenEls).find(k => screenEls[k] === el);
}

function showScreen(key, opts = {}) {
    const currentActive = Object.values(screenEls).find(el => el.classList.contains('active'));
    if (currentActive && idForScreen(currentActive) !== key && !opts.isBack) {
        screenHistory.push(idForScreen(currentActive));
    }
    Object.values(screenEls).forEach(el => el.classList.remove('active'));
    screenEls[key].classList.add('active');
}

function updateBadges() {
    setCrumb(crumbHandEl, studyHand);
    setCrumb(crumbHeroEl, studyHero);
    setCrumb(crumbScenarioEl, studyScenario ? SCENARIO_LABELS[studyScenario] : null);
    setCrumb(crumbVillainEl, studyVillain ? `vs ${studyVillain}` : null);
}

function setCrumb(el, text) {
    if (text) {
        el.textContent = text;
        el.hidden = false;
    } else {
        el.hidden = true;
    }
}

function resetStudy() {
    studyHand = null;
    studyHero = null;
    studyScenario = null;
    studyVillain = null;
    studyLegalScenarios = [];
    screenHistory = [];
    updateBadges();
    showScreen('hand', { isBack: true });
}

function goBack() {
    if (studyBusy) return;
    const prev = screenHistory.pop();
    if (!prev) return;
    if (prev === 'hand') { studyHero = null; studyScenario = null; studyVillain = null; }
    else if (prev === 'hero') { studyScenario = null; studyVillain = null; }
    else if (prev === 'scenario') { studyVillain = null; }
    updateBadges();
    showScreen(prev, { isBack: true });
}

document.querySelectorAll('[data-back]').forEach(btn => {
    btn.addEventListener('click', goBack);
});

document.getElementById('study-restart-btn').addEventListener('click', resetStudy);

// ---------------------------------------------------------------------------
// Hand grid (Step 0)
// ---------------------------------------------------------------------------

function renderStudyHandGrid() {
    const container = document.getElementById('study-grid');
    container.innerHTML = '';
    const cells = buildGrid();

    // Render in the same visual order as the full chart: row-major with
    // pairs on the diagonal, suited above, offsuit below.
    for (let r = 0; r < 13; r++) {
        for (let c = 0; c < 13; c++) {
            const cell = cells.find(g => g.row === r && g.col === c);
            const category = categorizeHand(cell.hand);
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `study-cell cat-${category}`;
            btn.textContent = cell.hand;
            btn.addEventListener('click', () => selectHand(cell.hand));
            container.appendChild(btn);
        }
    }
}

function selectHand(hand) {
    if (studyBusy) return;
    studyHand = hand;
    studyHero = null;
    studyScenario = null;
    studyVillain = null;
    updateBadges();
    showScreen('hero');
}

// ---------------------------------------------------------------------------
// Hero position (Step 1)
// ---------------------------------------------------------------------------

function renderHeroButtons() {
    const container = document.getElementById('study-hero-buttons');
    container.innerHTML = '';
    for (const pos of POSITIONS) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'choice-btn';
        btn.textContent = pos;
        btn.addEventListener('click', () => selectHero(pos));
        container.appendChild(btn);
    }
}

async function selectHero(hero) {
    if (studyBusy) return;
    studyBusy = true;
    try {
        studyHero = hero;
        studyScenario = null;
        studyVillain = null;
        updateBadges();

        const allFold = await step1AllFold(hero, studyHand);
        if (allFold) {
            showResult({ forcedFold: true, reason: 'never-profitable' });
            return;
        }
        studyLegalScenarios = SCENARIOS.filter(s => isScenarioLegalForHero(hero, s));
        renderScenarioButtons(studyLegalScenarios);
        showScreen('scenario');
    } finally {
        studyBusy = false;
    }
}

// ---------------------------------------------------------------------------
// Scenario (Step 2)
// ---------------------------------------------------------------------------

function renderScenarioButtons(scenarios) {
    const container = document.getElementById('study-scenario-buttons');
    container.innerHTML = '';
    for (const scenario of scenarios) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'choice-btn';
        btn.innerHTML = `${SCENARIO_LABELS[scenario]}<span class="choice-sub">${SCENARIO_SUBLABELS[scenario]}</span>`;
        btn.addEventListener('click', () => selectScenario(scenario));
        container.appendChild(btn);
    }
}

async function selectScenario(scenario) {
    if (studyBusy) return;
    studyBusy = true;
    try {
        studyScenario = scenario;
        studyVillain = null;
        updateBadges();

        const res = await step2AllFold(studyHero, scenario, studyHand);
        if (res.allFold) {
            showResult({
                forcedFold: true,
                reason: res.unreachable ? 'unreachable' : 'never-profitable-scenario'
            });
            return;
        }
        if (scenario === 'RFI') {
            const chartData = await loadChartFor(studyHero, null, 'RFI');
            showResult({ chartData });
            return;
        }
        if (res.villains.length === 1) {
            // Only one possible villain for this spot - skip straight to
            // the result instead of asking a question with one answer.
            await selectVillainCore(res.villains[0]);
            return;
        }
        renderVillainButtons(res.villains);
        showScreen('villain');
    } finally {
        studyBusy = false;
    }
}

// ---------------------------------------------------------------------------
// Villain position (Step 3)
// ---------------------------------------------------------------------------

function renderVillainButtons(villains) {
    const container = document.getElementById('study-villain-buttons');
    container.innerHTML = '';
    for (const pos of villains) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'choice-btn';
        btn.textContent = pos;
        btn.addEventListener('click', () => selectVillain(pos));
        container.appendChild(btn);
    }
}

/** Core logic shared by direct clicks and the single-villain auto-skip
 *  from selectScenario (which already holds the studyBusy lock). */
async function selectVillainCore(villain) {
    studyVillain = villain;
    updateBadges();
    const chartData = await loadChartFor(studyHero, villain, studyScenario);
    showResult({ chartData });
}

async function selectVillain(villain) {
    if (studyBusy) return;
    studyBusy = true;
    try {
        await selectVillainCore(villain);
    } finally {
        studyBusy = false;
    }
}

// ---------------------------------------------------------------------------
// Result screen
// ---------------------------------------------------------------------------

const resultTitleEl = document.getElementById('study-result-title');
const resultExplanationEl = document.getElementById('study-result-explanation');
const resultReachNoteEl = document.getElementById('study-result-reach-note');
const resultBreakdownEl = document.getElementById('study-result-breakdown');

// ---------------------------------------------------------------------------
// Dice roll assist
// ---------------------------------------------------------------------------

const diceWidgetEl = document.getElementById('dice-widget');
const diceTrackEl = document.getElementById('dice-track');
const diceMarkerEl = document.getElementById('dice-marker');
const diceBannerEl = document.getElementById('dice-banner');
const diceRollBtn = document.getElementById('dice-roll-btn');

let currentRollRows = null;

function buildDiceTrack(rows) {
    // Keep the marker element, drop any previously-built segments.
    diceTrackEl.querySelectorAll('.dice-segment').forEach(el => el.remove());
    for (const row of rows) {
        const seg = document.createElement('div');
        seg.className = `dice-segment ${row.key}`;
        seg.style.width = `${(row.pct * 100).toFixed(3)}%`;
        diceTrackEl.appendChild(seg);
    }
}

function resetDiceWidget(rows) {
    currentRollRows = rows;
    buildDiceTrack(rows);
    diceTrackEl.querySelectorAll('.dice-segment').forEach(el => el.classList.remove('landed'));
    resultBreakdownEl.querySelectorAll('.result-row').forEach(el => el.classList.remove('landed'));
    diceBannerEl.hidden = true;
    diceMarkerEl.classList.add('no-transition');
    diceMarkerEl.classList.remove('spinning', 'landing');
    diceMarkerEl.style.left = '0%';
    // Force a reflow so the next transition starts clean.
    void diceMarkerEl.offsetWidth;
    diceMarkerEl.classList.remove('no-transition');
    diceRollBtn.textContent = '\u{1F3B2} Roll the Dice';
    diceRollBtn.disabled = false;
}

function rollDice() {
    if (!currentRollRows || !currentRollRows.length || diceRollBtn.disabled) return;

    diceBannerEl.hidden = true;
    diceTrackEl.querySelectorAll('.dice-segment').forEach(el => el.classList.remove('landed'));
    resultBreakdownEl.querySelectorAll('.result-row').forEach(el => el.classList.remove('landed'));
    diceRollBtn.disabled = true;

    const roll = Math.random();
    let cumulative = 0;
    let winnerIdx = currentRollRows.length - 1;
    let winnerStart = 0;
    let winnerEnd = 1;
    for (let i = 0; i < currentRollRows.length; i++) {
        const start = cumulative;
        cumulative += currentRollRows[i].pct;
        if (roll < cumulative || i === currentRollRows.length - 1) {
            winnerIdx = i;
            winnerStart = start;
            winnerEnd = cumulative;
            break;
        }
    }
    // Land somewhere inside the winning segment (not dead-center every time).
    const landFrac = winnerStart + (winnerEnd - winnerStart) * (0.15 + Math.random() * 0.7);

    // Snap back to the start instantly (no visible transition), then animate
    // forward to the landing point on the next frame.
    diceMarkerEl.classList.add('no-transition');
    diceMarkerEl.classList.remove('landing');
    diceMarkerEl.style.left = '0%';
    void diceMarkerEl.offsetWidth;
    diceMarkerEl.classList.remove('no-transition');
    diceMarkerEl.classList.add('spinning');

    requestAnimationFrame(() => {
        diceMarkerEl.style.left = `${Math.min(99.5, Math.max(0.5, landFrac * 100)).toFixed(2)}%`;
    });

    setTimeout(() => {
        diceMarkerEl.classList.remove('spinning');
        diceMarkerEl.classList.add('landing');

        const segEls = diceTrackEl.querySelectorAll('.dice-segment');
        if (segEls[winnerIdx]) segEls[winnerIdx].classList.add('landed');
        const rowEls = resultBreakdownEl.querySelectorAll('.result-row');
        if (rowEls[winnerIdx]) rowEls[winnerIdx].classList.add('landed');

        const winner = currentRollRows[winnerIdx];
        diceBannerEl.textContent = `\u{1F3B2} Landed on: ${winner.name}`;
        diceBannerEl.className = `dice-banner ${winner.key}`;
        diceBannerEl.hidden = false;

        diceRollBtn.textContent = '\u{1F3B2} Roll Again';
        diceRollBtn.disabled = false;
    }, 560);
}

diceRollBtn.addEventListener('click', rollDice);

function showResult({ forcedFold, reason, chartData } = {}) {
    updateBadges();

    resultTitleEl.textContent = `${studyHand}`;
    resultBreakdownEl.innerHTML = '';

    let rows = [];
    let explanation = '';
    let reachNote = '';

    if (forcedFold) {
        rows = [{ name: 'Fold', pct: 1, key: 'fold' }];
        if (reason === 'unreachable') {
            explanation = `Hero would never realistically reach this spot with ${studyHand} \u2014 ` +
                `it doesn\u2019t fall on any line Hero would actually take. Effective decision: Fold.`;
        } else if (reason === 'never-profitable-scenario') {
            explanation = `${studyHand} is a guaranteed fold from ${studyHero} in every possible ` +
                `"${SCENARIO_LABELS[studyScenario]}" spot, no matter who Villain is.`;
        } else {
            explanation = `${studyHand} is a guaranteed fold from ${studyHero} in every situation Hero ` +
                `could realistically be in. No need to check further.`;
        }
    } else if (chartData) {
        const strategy = chartData.strategy;
        for (const actionObj of strategy.actions) {
            const range = parseUPI(strategy.upi_ranges[actionObj.name]);
            const freq = range[studyHand] || 0;
            rows.push({ name: actionObj.name, pct: freq, key: classifyAction(actionObj.name) });
        }

        // Charts for later nodes (vs 3-bet / 4-bet / 5-bet) store CONDITIONAL
        // frequencies, pre-multiplied by how often this hand actually reached
        // the node. K8o on the BTN facing a 3-bet is stored as fold:0.700
        // because BTN only opens K8o 70% of the time - the missing 30% is not
        // another action, it's the times the spot never happened. Rescale so
        // the numbers answer the real question: "given that I AM here, what
        // do I do?" This also keeps the dice roll correctly calibrated.
        const reach = rows.reduce((sum, r) => sum + r.pct, 0);

        if (reach <= 0.0001) {
            rows = [{ name: 'Fold', pct: 1, key: 'fold' }];
            explanation = `Hero never reaches this spot with ${studyHand} \u2014 it isn\u2019t in the ` +
                `range that gets here. Effective decision: Fold.`;
        } else {
            if (Math.abs(reach - 1) > 0.005) {
                rows = rows.map(r => ({ ...r, pct: r.pct / reach }));
                reachNote = `You only reach this spot with ${studyHand} about ` +
                    `${(reach * 100).toFixed(0)}% of the time \u2014 the rest of the time Hero ` +
                    `folded earlier. The breakdown below is what to do when you are here.`;
            }
            explanation = `${studyHand} as ${studyHero}` +
                (studyScenario === 'RFI' ? ' opening unopposed:' : ` ${SCENARIO_LABELS[studyScenario].toLowerCase()} from ${studyVillain}:`);
        }
    } else {
        rows = [{ name: 'Fold', pct: 1, key: 'fold' }];
        explanation = 'No chart data was found for this exact spot \u2014 defaulting to Fold.';
    }

    resultExplanationEl.textContent = explanation;

    if (reachNote) {
        resultReachNoteEl.textContent = reachNote;
        resultReachNoteEl.hidden = false;
    } else {
        resultReachNoteEl.textContent = '';
        resultReachNoteEl.hidden = true;
    }

    // Sort rows by descending frequency for a cleaner read.
    rows.sort((a, b) => b.pct - a.pct);

    for (const row of rows) {
        const rowEl = document.createElement('div');
        rowEl.className = `result-row ${row.key}`;
        rowEl.innerHTML = `
            <span class="result-label">${row.name}</span>
            <span class="result-bar-track"><span class="result-bar-fill" style="width:${(row.pct * 100).toFixed(1)}%"></span></span>
            <span class="result-pct">${(row.pct * 100).toFixed(1)}%</span>
        `;
        resultBreakdownEl.appendChild(rowEl);
    }

    // The dice roll assist only makes sense for a real chart lookup with
    // more than one possible action - a forced/fallback 100% Fold has
    // nothing interesting to roll for.
    const diceEnabled = !!chartData && rows.length > 1;
    if (diceEnabled) {
        diceWidgetEl.hidden = false;
        diceRollBtn.hidden = false;
        resetDiceWidget(rows);
    } else {
        diceWidgetEl.hidden = true;
        diceRollBtn.hidden = true;
        currentRollRows = null;
    }

    showScreen('result');
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

renderStudyHandGrid();
renderHeroButtons();
