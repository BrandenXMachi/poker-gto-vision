// GTO Preflop Trainer - Study Mode -> Postflop Playbook bridge
//
// Turns a completed Study-a-Hand result (hand, hero, villain, scenario,
// winning action) into a Postflop Playbook cell, deriving only what
// preflop history genuinely determines: IP/OOP, aggressor/caller role and
// pot type. Board texture and hand strength are NOT derived here - they
// depend on the flop and Hero's exact two cards (which suit, not just
// suited-or-not), which only the user actually knows. Those stay direct
// questions in postflop.js, same as the standalone flow, just landed on
// immediately after Position/Role are skipped.
//
// An earlier version of this file also tried to compute board texture and
// hand category from a manually-typed flop. It was removed: Study Mode
// hands only carry ranks and relative suitedness, never which suit, so
// flush-draw detection on a two-toned board had to guess whether Hero's
// suited card matched the paired suit - a silent, undisclosed assumption
// that could misclassify the hand. Asking the user directly (made hand /
// flush draw / straight draw - see PF_MADE_HAND etc. in postflop-lines.js)
// is both simpler and correct, since it needs no board parsing at all.
//
// Must load after app.js (POS_ORDER) and study.js (SCENARIOS).

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
// Entry point: build the postflop cell a completed Study result implies.
// Texture, made hand and draws are collected as direct questions next -
// see postflop.js's startPostflopFromBridge, which lands the user on the
// texture screen once this context is built.
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
 * cell once texture/made-hand/draws are answered.
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
