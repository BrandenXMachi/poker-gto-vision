// GTO Preflop Trainer - Study Mode -> Postflop Playbook bridge
//
// Turns a completed Study-a-Hand result (hand, hero, villain, scenario,
// winning action) into a Postflop Playbook cell, asking only for what
// preflop history genuinely cannot supply: the flop itself. Everything
// else - IP/OOP, aggressor/caller role, pot type, and (once the board is
// known) board texture and hand category - is derived, not asked.
//
// Must load after app.js (POS_ORDER), study.js (SCENARIOS) and
// postflop-lines.js (PF_TEXTURES/PF_CATEGORIES ids this maps onto).

// ---------------------------------------------------------------------------
// IP / OOP
// ---------------------------------------------------------------------------

/** Postflop acting order is NOT the same as preflop order: the blinds act
 *  first postflop regardless of when they acted preflop. Everyone else
 *  keeps their preflop order. */
const POSTFLOP_ORDER = { SB: 0, BB: 1, UTG: 2, MP: 3, CO: 4, BTN: 5 };

function deriveIpOop(heroPos, villainPos) {
    if (!heroPos || !villainPos) return null;
    return POSTFLOP_ORDER[heroPos] > POSTFLOP_ORDER[villainPos] ? 'IP' : 'OOP';
}

// ---------------------------------------------------------------------------
// Role (aggressor/caller) + pot type, from scenario + which action won
// ---------------------------------------------------------------------------

/**
 * `scenario` is one of Study Mode's SCENARIOS; `actionKey` is the winning
 * row's classifyAction() result ('raise' | 'call' | 'fold'). Returns
 * { role, potType } or null when there is no postflop decision left to
 * guide (fold, or an all-in scenario where the money is already in).
 */
function deriveRoleAndPotType(scenario, actionKey) {
    if (actionKey === 'fold') return null;

    if (scenario === 'RFI') {
        // Hero opens; a raise here only becomes a "pot" once someone calls,
        // which Study Mode does not track. Treat Hero as the presumptive
        // aggressor of a single-raised pot - the common case by far.
        return actionKey === 'raise' ? { role: 'aggressor', potType: 'single-raised' } : null;
    }
    if (scenario === 'vs_Open') {
        if (actionKey === 'call') return { role: 'caller', potType: 'single-raised' };
        if (actionKey === 'raise') return { role: 'aggressor', potType: '3bet' };
    }
    if (scenario === 'vs_3B') {
        if (actionKey === 'call') return { role: 'caller', potType: '3bet' };
        if (actionKey === 'raise') return { role: 'aggressor', potType: '4bet' };
    }
    if (scenario === 'vs_4B') {
        if (actionKey === 'call') return { role: 'caller', potType: '4bet' };
        // Raising here is a 5-bet shove - no postflop street remains.
        return null;
    }
    if (scenario === 'vs_5B') {
        // Calling or shoving over a 5-bet is effectively all-in - no more
        // postflop decisions to guide.
        return null;
    }
    return null;
}

/** True when a completed Study Mode result has a postflop street left to
 *  play, i.e. "Continue to Postflop" should be offered at all. */
function studyResultHasPostflop(scenario, actionKey) {
    return deriveRoleAndPotType(scenario, actionKey) !== null;
}

// ---------------------------------------------------------------------------
// Board texture + hand category, computed from the entered flop
// ---------------------------------------------------------------------------

const BRIDGE_RANK_VALUE = {
    A: 14, K: 13, Q: 12, J: 11, T: 10, '9': 9, '8': 8, '7': 7,
    '6': 6, '5': 5, '4': 4, '3': 3, '2': 2
};

/** Parse a board string like "Jh Ts 6c" or "JhTs6c" into [{rank,suit,value}]. */
function parseBoard(str) {
    const cleaned = str.replace(/\s+/g, '').toUpperCase();
    const cards = [];
    for (let i = 0; i < cleaned.length; i += 2) {
        const rank = cleaned[i];
        const suit = cleaned[i + 1];
        if (!(rank in BRIDGE_RANK_VALUE) || !'SHDC'.includes(suit)) return null;
        cards.push({ rank, suit, value: BRIDGE_RANK_VALUE[rank] });
    }
    return cards.length === 3 ? cards : null;
}

/** Classify a 3-card flop into one of PF_TEXTURES' ids: wet / dry / ultradry. */
function classifyBoardTexture(board) {
    const suits = board.map((c) => c.suit);
    const suitCounts = {};
    for (const s of suits) suitCounts[s] = (suitCounts[s] || 0) + 1;
    const flushDrawPossible = Math.max(...Object.values(suitCounts)) >= 2;

    const values = board.map((c) => c.value).sort((a, b) => a - b);
    // "Connected" here means close enough for straights/gutters to matter
    // (one-gappers or tighter) - a wider gap like 8-5-2 has no realistic
    // straight-draw texture even though it technically spans <=4.
    const connected = (values[1] - values[0] <= 2) || (values[2] - values[1] <= 2);
    const highCard = values[2];
    const hasBroadway = highCard >= 11;

    if ((flushDrawPossible || connected) && highCard >= 8) return 'wet';
    if (!flushDrawPossible && !connected && !hasBroadway) return 'ultradry';
    return 'dry';
}

/**
 * Classify Hero's hand against the board into one of PF_CATEGORIES' ids
 * (1 nut value, 2 medium value, 3 semi-bluff draw, 4 air). `hand` is a
 * Study Mode hand string like "AKo", "77", "JTs" - it names ranks and
 * suitedness but not exact suits, so a flush draw is only credited when the
 * hand is suited AND the board has two-of-a-suit (the friendlier case is
 * assumed rather than a guaranteed one - stated in the UI note).
 */
function classifyHandCategory(hand, board) {
    const isPair = hand.length === 2;
    const r1 = hand[0], r2 = isPair ? hand[0] : hand[1];
    const suited = !isPair && hand[2] === 's';
    const v1 = BRIDGE_RANK_VALUE[r1];
    const v2 = BRIDGE_RANK_VALUE[r2];

    const boardValues = board.map((c) => c.value);
    const boardSet = new Set(boardValues);
    const topBoard = Math.max(...boardValues);

    const suitCounts = {};
    for (const c of board) suitCounts[c.suit] = (suitCounts[c.suit] || 0) + 1;
    const boardTwoToned = Math.max(...Object.values(suitCounts)) >= 2;

    if (isPair) {
        if (v1 > topBoard) return 1;       // overpair
        if (boardSet.has(v1)) return 1;    // set
        if (v1 >= topBoard - 2) return 2;  // underpair close enough to showdown
        return 4;                          // small pair well under the board
    }

    const madePairRanks = [v1, v2].filter((v) => boardSet.has(v));
    if (madePairRanks.length) {
        const madeTop = Math.max(...madePairRanks);
        return madeTop >= topBoard ? 1 : 2; // top pair vs a lower/second pair
    }

    // No pair yet: strong draw?
    const sorted = [v1, v2, ...boardValues].sort((a, b) => a - b);
    let hasStraightDraw = false;
    for (let i = 0; i + 3 < sorted.length; i++) {
        if (sorted[i + 3] - sorted[i] <= 4) { hasStraightDraw = true; break; }
    }
    const hasFlushDraw = suited && boardTwoToned;
    if (hasFlushDraw || hasStraightDraw) return 3;

    return 4; // air
}

// ---------------------------------------------------------------------------
// Entry point: build the postflop cell a completed Study result implies,
// minus the board (which the caller collects next and merges in).
// ---------------------------------------------------------------------------

const POT_TYPE_LABELS = {
    'single-raised': 'Single-raised pot',
    '3bet': '3-bet pot',
    '4bet': '4-bet pot'
};

/**
 * Returns null when there is no postflop decision to guide (fold, or the
 * money is already all-in), otherwise:
 *   { position, role, heroPos, villainPos, potType, potTypeLabel }
 * `position`/`role` are ready to merge straight into a Postflop Playbook
 * cell once texture/category are added from the board.
 */
function buildBridgeContext(heroPos, villainPos, scenario, actionKey) {
    const roleInfo = deriveRoleAndPotType(scenario, actionKey);
    if (!roleInfo) return null;
    const position = deriveIpOop(heroPos, villainPos);
    if (!position) return null;
    return {
        position,
        role: roleInfo.role,
        heroPos,
        villainPos,
        potType: roleInfo.potType,
        potTypeLabel: POT_TYPE_LABELS[roleInfo.potType] || roleInfo.potType
    };
}
