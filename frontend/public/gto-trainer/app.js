// GTO Preflop Trainer - Web App
// Loads validated GTO chart data and renders a 13x13 hand grid.

const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
const POSITIONS = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'];

// Position order for determining who acts first (lower = acts earlier preflop)
const POS_ORDER = { UTG: 0, MP: 1, CO: 2, BTN: 3, SB: 4, BB: 5 };

// Cache for loaded JSON data (also caches misses as `null`)
const dataCache = {};

// Current selection state
let state = {
    hero: 'BTN',
    villain: 'BB',
    scenario: 'RFI'
};

// DOM elements
const heroSelect = document.getElementById('hero-pos');
const villainSelect = document.getElementById('villain-pos');
const scenarioSelect = document.getElementById('scenario');
const chartEl = document.getElementById('chart');
const chartTitle = document.getElementById('chart-title');
const tooltipEl = document.getElementById('tooltip');

// Keep the dropdowns in sync with the initial state.
heroSelect.value = state.hero;
villainSelect.value = state.villain;
scenarioSelect.value = state.scenario;

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

async function loadJSON(path) {
    if (path in dataCache) return dataCache[path];
    let data = null;
    try {
        const resp = await fetch(path);
        if (resp.ok) {
            data = await resp.json();
        }
    } catch (e) {
        data = null;
    }
    dataCache[path] = data;
    return data;
}

/** Return the standard open-raise size string for a position. */
function openSizeFor(pos) {
    return pos === 'SB' ? '3.0bb' : '2.5bb';
}

// Candidate 3-bet / 4-bet sizes observed in the reference chart data.
// Sizing varies slightly depending on which positions are involved, so
// rather than hard-coding every combination we just try each plausible
// size until we find a file that exists.
const BET3_CANDIDATES = ['11.0bb', '9.0bb', '8.5bb'];
const BET4_CANDIDATES = ['20.0bb', '21.0bb', '22.0bb', '24.0bb', '25.0bb'];

/**
 * Find the chart file path(s) for a given scenario/hero/villain combo.
 * Returns a string, an array of candidate strings (tried in order until
 * one loads successfully), or null if the combination is not valid for
 * this scenario (e.g. wrong position order).
 */
function findChartPath(hero, villain, scenario) {
    if (scenario === 'RFI') {
        // RFI: hero opens unopposed. BB can never face an RFI decision
        // (everyone folds to BB just means BB wins the blinds).
        if (hero === 'BB') return null;
        return `data/RFI/${hero}/${hero}.json`;
    }

    if (hero === villain) return null;

    if (scenario === 'vs_Open') {
        // Villain opened, hero faces the open. Villain must act before hero.
        if (POS_ORDER[villain] >= POS_ORDER[hero]) return null;
        const openSize = openSizeFor(villain);
        return `data/vs_Open/${hero}/${villain}_${openSize}_${hero}.json`;
    }

    if (scenario === 'vs_3B') {
        // Hero opened, villain 3-bet, hero faces the 3-bet.
        // Hero must act (and open) before villain, and BB can't open.
        if (hero === 'BB') return null;
        if (POS_ORDER[hero] >= POS_ORDER[villain]) return null;
        const openSize = openSizeFor(hero);
        return BET3_CANDIDATES.map(bet3 =>
            `data/vs_3B/${hero}/${hero}_${openSize}_${villain}_${bet3}_${hero}.json`);
    }

    if (scenario === 'vs_4B') {
        // Villain opened, hero 3-bet, villain 4-bet, hero faces the 4-bet.
        // Villain must act (and open) before hero, and BB can't open.
        if (villain === 'BB') return null;
        if (POS_ORDER[villain] >= POS_ORDER[hero]) return null;
        const openSize = openSizeFor(villain);
        const paths = [];
        for (const bet3 of BET3_CANDIDATES) {
            for (const bet4 of BET4_CANDIDATES) {
                paths.push(`data/vs_4B/${hero}/${villain}_${openSize}_${hero}_${bet3}_${villain}_${bet4}_${hero}.json`);
            }
        }
        return paths;
    }

    if (scenario === 'vs_5B') {
        // Hero opened, villain 3-bet, hero 4-bet, villain shoved (5-bet
        // all-in), hero faces the shove. Same roles as vs_3B.
        if (hero === 'BB') return null;
        if (POS_ORDER[hero] >= POS_ORDER[villain]) return null;
        const openSize = openSizeFor(hero);
        const paths = [];
        for (const bet3 of BET3_CANDIDATES) {
            for (const bet4 of BET4_CANDIDATES) {
                paths.push(`data/vs_5B/${hero}/${hero}_${openSize}_${villain}_${bet3}_${hero}_${bet4}_${villain}_AllIn_${hero}.json`);
            }
        }
        return paths;
    }

    return null;
}

/** Human-readable explanation for why a combination has no chart. */
function explainNoChart(hero, villain, scenario) {
    if (scenario === 'RFI' && hero === 'BB') {
        return 'BB has no RFI decision - everyone folded means BB just wins the blinds.';
    }
    if (hero === villain) {
        return 'Hero and Villain must be different positions.';
    }
    if (scenario === 'vs_Open' && POS_ORDER[villain] >= POS_ORDER[hero]) {
        return `${villain} acts after ${hero}, so ${villain} can't have opened before ${hero}'s decision.`;
    }
    if (scenario === 'vs_3B') {
        if (hero === 'BB') return 'BB can never be the opener facing a 3-bet.';
        if (POS_ORDER[hero] >= POS_ORDER[villain]) {
            return `${hero} must act (and open) before ${villain} to face a 3-bet from them.`;
        }
    }
    if (scenario === 'vs_4B' || scenario === 'vs_5B') {
        if (villain === 'BB' && scenario === 'vs_4B') return 'BB can never be the opener facing a 4-bet.';
        if (scenario === 'vs_4B' && POS_ORDER[villain] >= POS_ORDER[hero]) {
            return `${villain} must act (and open) before ${hero} for ${hero} to 3-bet and face a 4-bet.`;
        }
        if (scenario === 'vs_5B') {
            if (hero === 'BB') return 'BB can never be the opener facing a 5-bet.';
            if (POS_ORDER[hero] >= POS_ORDER[villain]) {
                return `${hero} must act (and open) before ${villain} to face a 5-bet shove from them.`;
            }
        }
    }
    return 'No chart data available for this scenario.';
}

// ---------------------------------------------------------------------------
// UPI range parsing
// ---------------------------------------------------------------------------

/**
 * Parse a UPI range string like "AA:1.000,A2s:1.000,A3o:0.016,..."
 * Returns a map: handName -> frequency (0-1)
 */
function parseUPI(upiString) {
    const result = {};
    if (!upiString) return result;
    const parts = upiString.split(',');
    for (const part of parts) {
        const [hand, freq] = part.split(':');
        if (hand && freq !== undefined) {
            result[hand] = parseFloat(freq);
        }
    }
    return result;
}

// ---------------------------------------------------------------------------
// Chart rendering
// ---------------------------------------------------------------------------

/**
 * Build the 13x13 grid data, matching the standard poker hand-matrix
 * layout: AA in the top-left corner, 22 in the bottom-right corner,
 * suited combos above the diagonal, offsuit combos below it.
 *
 * RANKS is ordered A..2 (index 0 = highest rank, index 12 = lowest).
 * For any two distinct ranks, whichever has the SMALLER index is the
 * higher card, and hand names must always list the higher-ranked card
 * first (e.g. "AKo", never "KAo").
 *
 * Returns an array of {row, col, hand, type} where type is 'pair', 'suited', 'offsuit'
 */
function buildGrid() {
    const cells = [];
    for (let r = 0; r < 13; r++) {
        for (let c = 0; c < 13; c++) {
            if (r === c) {
                // Diagonal: pocket pair
                cells.push({ row: r, col: c, hand: RANKS[r] + RANKS[r], type: 'pair' });
            } else if (r < c) {
                // Upper-right triangle: suited combos.
                // r has the smaller index -> higher rank -> listed first.
                cells.push({ row: r, col: c, hand: RANKS[r] + RANKS[c] + 's', type: 'suited' });
            } else {
                // Lower-left triangle: offsuit combos.
                // c has the smaller index -> higher rank -> listed first.
                cells.push({ row: r, col: c, hand: RANKS[c] + RANKS[r] + 'o', type: 'offsuit' });
            }
        }
    }
    return cells;
}

/**
 * Get the dominant action color for a hand based on frequencies.
 * Returns {color, raisePct, callPct, foldPct, dominant}
 */
function getActionColors(handData) {
    const raise = handData.raise || 0;
    const call = handData.call || 0;
    const fold = handData.fold || 0;

    // Determine dominant action
    let dominant = 'fold';
    let dominantPct = fold;
    if (raise > dominantPct) { dominant = 'raise'; dominantPct = raise; }
    if (call > dominantPct) { dominant = 'call'; dominantPct = call; }

    // Color intensity based on frequency
    const intensity = Math.min(1, dominantPct * 1.5);

    let color;
    if (dominant === 'raise') {
        color = `rgba(76, 175, 80, ${0.3 + intensity * 0.7})`;
    } else if (dominant === 'call') {
        color = `rgba(33, 150, 243, ${0.3 + intensity * 0.7})`;
    } else {
        color = `rgba(244, 67, 54, ${0.3 + intensity * 0.7})`;
    }

    return { color, raise, call, fold, dominant };
}

/**
 * Render the chart for the current state.
 */
async function renderChart() {
    const { hero, villain, scenario } = state;

    // Find the chart file
    let paths = findChartPath(hero, villain, scenario);
    if (!paths) {
        const scenarioLabel = {
            RFI: 'Unopened',
            vs_Open: `Facing ${villain} Open`,
            vs_3B: `Facing ${villain} 3-Bet`,
            vs_4B: `Facing ${villain} 4-Bet`,
            vs_5B: `Facing ${villain} 5-Bet`
        }[scenario] || scenario;
        chartTitle.textContent = `${hero} ${scenarioLabel}`;
        chartEl.innerHTML = `<div class="chart-message">${explainNoChart(hero, villain, scenario)}</div>`;
        return;
    }
    if (!Array.isArray(paths)) paths = [paths];

    // Try each candidate path
    let chartData = null;
    for (const p of paths) {
        const data = await loadJSON(p);
        if (data) {
            chartData = data;
            break;
        }
    }

    if (!chartData) {
        chartTitle.textContent = `${hero} vs ${villain} - ${scenario}`;
        chartEl.innerHTML = '<div class="chart-message">No chart data available for this scenario</div>';
        return;
    }

    // Parse the strategy
    const strategy = chartData.strategy;
    const actions = strategy.actions.map(a => a.name);
    const upiRanges = strategy.upi_ranges;

    // Build per-hand action frequencies. Any aggressive action (opening
    // raise, 3-bet, 4-bet, all-in shove, etc.) is bucketed as "raise";
    // "call" and "fold" are detected by name.
    const handFreqs = {};
    for (const action of actions) {
        const range = parseUPI(upiRanges[action]);
        for (const [hand, freq] of Object.entries(range)) {
            if (!handFreqs[hand]) handFreqs[hand] = {};
            const lower = action.toLowerCase();
            const actionKey = lower.includes('fold') ? 'fold'
                : lower.includes('call') ? 'call'
                : 'raise';
            handFreqs[hand][actionKey] = (handFreqs[hand][actionKey] || 0) + freq;
        }
    }

    // Update title
    const scenarioLabel = {
        'RFI': 'Unopened',
        'vs_Open': `Facing ${villain} Open`,
        'vs_3B': `Facing ${villain} 3-Bet`,
        'vs_4B': `Facing ${villain} 4-Bet`,
        'vs_5B': `Facing ${villain} 5-Bet`
    }[scenario];
    chartTitle.textContent = `${hero} ${scenarioLabel}`;

    // Build the grid
    const grid = buildGrid();
    chartEl.innerHTML = '';

    // Add column headers (top row). First cell is a blank corner cell,
    // then one label per rank column (A..2), giving 14 cells total to
    // match the 14-column CSS grid (1 label column + 13 rank columns).
    chartEl.appendChild(createLabelCell(''));
    for (const rank of RANKS) {
        chartEl.appendChild(createLabelCell(rank));
    }

    // Add rows
    for (let r = 0; r < 13; r++) {
        // Row label
        chartEl.appendChild(createLabelCell(RANKS[r]));

        for (let c = 0; c < 13; c++) {
            const cell = grid.find(g => g.row === r && g.col === c);
            if (!cell) {
                chartEl.appendChild(createEmptyCell());
                continue;
            }

            const handData = handFreqs[cell.hand] || { raise: 0, call: 0, fold: 0 };
            const { color, raise, call, fold } = getActionColors(handData);

            const cellEl = document.createElement('div');
            cellEl.className = 'cell';
            cellEl.style.background = color;
            cellEl.textContent = cell.hand;
            cellEl.dataset.hand = cell.hand;
            cellEl.dataset.raise = raise.toFixed(3);
            cellEl.dataset.call = call.toFixed(3);
            cellEl.dataset.fold = fold.toFixed(3);

            cellEl.addEventListener('mouseenter', (e) => showTooltip(e, cell.hand, raise, call, fold));
            cellEl.addEventListener('mousemove', (e) => moveTooltip(e));
            cellEl.addEventListener('mouseleave', hideTooltip);

            chartEl.appendChild(cellEl);
        }
    }
}

function createLabelCell(text) {
    const el = document.createElement('div');
    el.className = 'cell cell-label';
    el.textContent = text;
    return el;
}

function createEmptyCell() {
    const el = document.createElement('div');
    el.className = 'cell empty';
    return el;
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function showTooltip(e, hand, raise, call, fold) {
    const tooltip = tooltipEl;
    tooltip.innerHTML = `
        <div class="hand-name">${hand}</div>
        <div class="action-row"><span class="action-name">Raise</span><span class="action-pct raise">${(raise * 100).toFixed(1)}%</span></div>
        <div class="action-row"><span class="action-name">Call</span><span class="action-pct call">${(call * 100).toFixed(1)}%</span></div>
        <div class="action-row"><span class="action-name">Fold</span><span class="action-pct fold">${(fold * 100).toFixed(1)}%</span></div>
    `;
    tooltip.style.display = 'block';
    moveTooltip(e);
}

function moveTooltip(e) {
    const tooltip = tooltipEl;
    const x = e.clientX + 15;
    const y = e.clientY + 15;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}

function hideTooltip() {
    tooltipEl.style.display = 'none';
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

function updateState() {
    state.hero = heroSelect.value;
    state.villain = villainSelect.value;
    state.scenario = scenarioSelect.value;
    renderChart();
}

heroSelect.addEventListener('change', updateState);
villainSelect.addEventListener('change', updateState);
scenarioSelect.addEventListener('change', updateState);

// Initial render
renderChart();
