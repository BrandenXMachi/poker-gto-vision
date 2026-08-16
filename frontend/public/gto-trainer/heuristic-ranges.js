// ===========================================================================
// HEURISTIC RANGES - NOT SOLVER OUTPUT
// ===========================================================================
//
// Everything under data/ is solver output. Nothing in THIS file is. These are
// hand-specified ranges for "Facing an Open + a Caller" in the seats where the
// upstream solve has no chart at all, so that the app can answer the question
// instead of going silent.
//
// Provenance: drafted by the project owner (2026-08-16), then adjusted here to
// fit the frequencies measured off the six solved open+caller charts we do
// have. That measurement (all 169 hand classes x 6 chart pairs) found:
//
//   - raise frequency barely moves when a caller appears: -1.1% on average,
//     up in 66 hand-spots and down in 146
//   - the calling range collapses by about a third (BB: 21% -> 15%)
//   - folding absorbs the difference, up 6-8 points of total range
//
// So these ranges are built to land near a 4-7% raise frequency, with the
// calling range doing the position-dependent work. Combo percentages are noted
// per seat below so the calibration can be re-checked.
//
// Two limits worth stating plainly:
//
//   1. These are OPENER-AGNOSTIC. One range per seat stands in for every
//      opener, but the solved charts show the opener matters a lot (BB raise
//      frequency runs 6.3% / 7.7% / 10.1% against UTG / MP / CO). The UI says
//      so on every estimated result.
//   2. These are PURE ranges - each hand does one thing. Real solved charts
//      mix. That is why the dice roll is hidden on these results: there is
//      nothing to randomise, and a die that always lands the same way would
//      imply a precision that isn't here.
//
// If a solved chart exists for a spot, it wins. This file is only ever
// consulted where data/ has nothing.

const HEURISTIC_META = {
    kind: 'heuristic',
    source: 'hand-specified, calibrated against the 6 solved open+caller charts'
};

const RANKS_H = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];

/** All 169 hand classes, so anything not named below can be folded explicitly
 *  rather than being silently absent. */
function allHandClasses() {
    const out = [];
    for (let i = 0; i < RANKS_H.length; i++) {
        for (let j = 0; j < RANKS_H.length; j++) {
            if (i === j) out.push(RANKS_H[i] + RANKS_H[i]);
            else if (i < j) out.push(RANKS_H[i] + RANKS_H[j] + 's');
            else out.push(RANKS_H[j] + RANKS_H[i] + 'o');
        }
    }
    return [...new Set(out)];
}

// ---------------------------------------------------------------------------
// The ranges. Written out hand by hand rather than as "JJ+" shorthand: a
// notation parser is one more thing to get wrong, and every hand here should
// be individually arguable.
// ---------------------------------------------------------------------------

const HEURISTIC_RANGES = {
    // CO faces UTG open + MP call with three seats still behind (BTN, SB, BB).
    // Tightest of the four: most likely to get squeezed, worst position odds.
    // raise 52 combos (3.9%), call 44 (3.3%)
    CO: {
        raiseSize: '10.0bb',
        raise: ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo', 'AQs', 'A5s', 'A4s'],
        call: ['TT', '99', 'AQo', 'AJs', 'KQs', 'JTs', 'T9s', '98s']
    },

    // BTN has position on everyone for the rest of the hand, which is what
    // buys the wide calling range - the widest of the four.
    // raise 48 combos (3.6%), call 102 (7.7%)
    BTN: {
        raiseSize: '10.0bb',
        raise: ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo', 'AQs', 'A5s'],
        call: ['TT', '99', '88', '77', '66', '55', '44', '33', '22',
               'AJs', 'ATs', 'KQs', 'KJs', 'QJs', 'JTs', 'T9s', '98s', '87s',
               'AQo']
    },

    // SB is out of position on everyone with the BB still to act. The solved
    // SB charts have no Call action at all in this shape, so this one is
    // raise-or-fold too - that is consistent with the data, not an omission.
    // raise 86 combos (6.5%), call 0%
    SB: {
        raiseSize: '12.0bb',
        raise: ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88',
                'AKs', 'AKo', 'AQs', 'AJs', 'ATs', 'KQs',
                'A5s', 'A4s', 'A3s'],
        call: []
    },

    // BB closes the action and is already 1bb in, so it defends widest by
    // calling. Matches the measured post-caller BB calling range (~15%).
    // raise 84 combos (6.3%), call 174 (13.1%)
    BB: {
        raiseSize: '12.0bb',
        raise: ['AA', 'KK', 'QQ', 'JJ', 'TT', '99',
                'AKs', 'AKo', 'AQs', 'AJs', 'KQs', 'KJs',
                'A5s', 'A4s', 'A3s', 'A2s'],
        call: ['88', '77', '66', '55', '44', '33', '22',
               'ATs', 'A9s', 'A8s', 'A7s', 'A6s',
               'KTs', 'QTs', 'QJs', 'JTs', 'T9s',
               '98s', '87s', '76s', '65s', '54s',
               'J9s', 'T8s', '97s',
               'AQo', 'AJo', 'ATo', 'KQo', 'KJo']
    }
};

/** Sanity guard: a hand appearing in both lists would render as whichever
 *  action happened to be read last, which is exactly the kind of silent
 *  wrongness this file must not have. Logs loudly instead. */
function assertNoOverlap() {
    for (const [seat, def] of Object.entries(HEURISTIC_RANGES)) {
        const dupes = def.raise.filter((h) => def.call.includes(h));
        if (dupes.length) {
            console.error(
                `heuristic-ranges: ${seat} lists ${dupes.join(', ')} as both ` +
                'raise and call. One action per hand.'
            );
        }
    }
}
assertNoOverlap();

/** Build a chart object shaped exactly like a solved one, so every existing
 *  renderer, frequency calculator and result path works on it untouched.
 *  The __heuristic flag is what the UI keys its badge off. */
function buildHeuristicChart(hero) {
    const def = HEURISTIC_RANGES[hero];
    if (!def) return null;

    const raiseName = `Raise ${def.raiseSize}`;
    const folds = allHandClasses().filter(
        (h) => !def.raise.includes(h) && !def.call.includes(h)
    );

    const upi = (hands) => hands.map((h) => `${h}:1.0`).join(',');

    const actions = [{ name: raiseName }];
    if (def.call.length) actions.push({ name: 'Call' });
    actions.push({ name: 'Fold' });

    const upi_ranges = { [raiseName]: upi(def.raise), Fold: upi(folds) };
    if (def.call.length) upi_ranges.Call = upi(def.call);

    return {
        __heuristic: true,
        __meta: HEURISTIC_META,
        strategy: { actions, upi_ranges }
    };
}

/** Which seats can face an open plus a cold-call at all. UTG and MP are
 *  excluded because nobody acts before them who could have called a raise. */
function heuristicSeats() {
    return Object.keys(HEURISTIC_RANGES);
}
