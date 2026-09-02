// ===========================================================================
// POSTFLOP PLAYBOOK - HEURISTIC FRAMEWORK, NOT SOLVER OUTPUT
// ===========================================================================
//
// Nothing in this file comes from the solve that produced web/data/. This is
// a coaching framework: ten named lines, chosen by archetype rather than by
// solved frequency. It is deliberately a different tier of claim from the
// preflop charts, and the UI says so on every screen it drives.
//
// The source material described the ten lines by position, board texture and
// hand category. Mapping those onto a filter funnel surfaced three things
// worth recording here, because they shaped the whole structure:
//
//   1. A FIFTH AXIS IS LOAD-BEARING AND WAS UNNAMED: who raised preflop.
//      V1/V2/V3 are continuation-bet lines - Hero is the aggressor. V4, V5,
//      B3, B4 and B5 all open with a check-call, check-raise or float, so
//      Hero is the caller. Without that axis, a check-raise and a c-bet
//      collapse into the same cell, and they are not the same spot.
//
//   2. THE TEN LINES COVER ROUGHLY HALF THE SPACE. 2 positions x 2 roles x
//      3 textures x 4 categories = 48 cells; the ten lines match about 24.
//      Category 4 (air) has almost no line at all, which is correct - air
//      folds - but a funnel that dead-ends on a blank screen reads as broken.
//      So every uncovered cell falls through to a PF_DEFAULTS policy that is
//      badged DEFAULT and never presented as one of the ten.
//
//   3. SOME CELLS MATCH SEVERAL LINES, AND THAT IS INFORMATION. OOP as the
//      caller with a Category 1 hand on a wet board matches both V4 and V5 -
//      but V4 needs villain to bet the flop and V5 needs villain to check it
//      back. Rather than silently picking one, the UI asks which happened.
//      Each line carries a `trigger` string for exactly that question.
//
// Sizings are given as fractions of pot, as in the source. Every line here
// assumes a heads-up pot and ignores stack depth / SPR - see PF_SCOPE_NOTE.

// ---------------------------------------------------------------------------
// The axes
// ---------------------------------------------------------------------------

const PF_POSITIONS = [
    { id: 'IP', label: 'In Position', sub: 'You act last on every street' },
    { id: 'OOP', label: 'Out of Position', sub: 'You act first on every street' }
];

const PF_ROLES = [
    {
        id: 'aggressor',
        label: 'I raised preflop',
        sub: 'You hold the betting lead - villain called you'
    },
    {
        id: 'caller',
        label: 'I called preflop',
        sub: 'Villain holds the betting lead - you called their raise'
    }
];

// Example boards are the ones named in the source material where it named
// them, so the categories stay anchored to something concrete rather than to
// the words "wet" and "dry", which beginners read very differently.
const PF_TEXTURES = [
    {
        id: 'wet',
        label: 'Wet / Dynamic',
        example: 'J\u2660 T\u2660 6\u2665',
        sub: 'Two suited or connected cards - many draws are live, and your equity can be overtaken'
    },
    {
        id: 'dry',
        label: 'Dry / Static',
        example: 'A\u2660 7\u2666 2\u2663',
        sub: 'Rainbow and disconnected, but with a high card villain can pair and call with'
    },
    {
        id: 'ultradry',
        label: 'Ultra-Dry',
        example: '8\u2663 5\u2666 2\u2665',
        sub: 'Rainbow, disconnected and low - villain rarely holds anything worth continuing with'
    }
];

const PF_CATEGORIES = [
    {
        id: 1,
        label: 'Category 1 - Nut Value',
        sub: 'Top pair top kicker or better: overpairs, two pair, sets, straights, flushes'
    },
    {
        id: 2,
        label: 'Category 2 - Medium Value',
        sub: 'Showdown value that does not want a big pot: second pair, weak top pair, underpairs'
    },
    {
        id: 3,
        label: 'Category 3 - Semi-Bluff',
        sub: 'High-equity draws: flush draws, open-enders, combo draws'
    },
    {
        id: 4,
        label: 'Category 4 - Air',
        sub: 'No pair, no draw. Backdoors and blockers at best'
    }
];

// Shown once, up front. Both limits are real and neither is recoverable by
// picking a different line, so they belong before the funnel rather than
// buried in a result.
const PF_SCOPE_NOTE =
    'Every line here assumes a heads-up pot and ignores stack depth. Multiway ' +
    'pots and short stacks change the correct answer substantially, and this ' +
    'framework has nothing to say about either.';

const PF_PROVENANCE_NOTE =
    'The Postflop Playbook is a heuristic coaching framework, not solver ' +
    'output. Unlike the preflop charts, none of it was solved - it is a set of ' +
    'named archetype lines chosen for being teachable and broadly sound.';

// ---------------------------------------------------------------------------
// The ten lines
// ---------------------------------------------------------------------------

const POSTFLOP_LINES = [
    {
        id: 'V1',
        name: 'Triple Barrel Fast-Play',
        kind: 'value',
        match: { position: ['IP', 'OOP'], role: ['aggressor'], texture: ['wet'], category: [1] },
        trigger: 'Villain calls your flop bet',
        idea: 'On a board this dynamic, a hand that is best now often will not be ' +
              'best by the river. Charge the draws every street rather than ' +
              'protecting a pot you might lose the lead in.',
        streets: [
            { street: 'Flop', action: 'Bet', size: '50% pot',
              why: 'Enough to make draws pay, small enough to keep worse pairs calling.' },
            { street: 'Turn', action: 'Bet', size: '75% pot',
              why: 'The turn is where draws are priced out. This is the barrel that earns the money.' },
            { street: 'River', action: 'Bet', size: '75% pot',
              why: 'Missed draws cannot call, but the pairs you charged along the way often can.' }
        ],
        failsWhen: 'The obvious draw completes and villain suddenly raises. A ' +
                   'nut hand on the flop can be second best on the river - this ' +
                   'line does not tell you to fold, and sometimes you should.'
    },
    {
        id: 'V2',
        name: 'Delayed C-Bet / Pot Control',
        kind: 'value',
        match: { position: ['IP', 'OOP'], role: ['aggressor'], texture: ['dry', 'ultradry'], category: [2] },
        trigger: 'You have showdown value you do not want to play a big pot with',
        idea: 'A medium-strength hand wins a medium pot. Betting three streets ' +
              'with it only gets called by better - so keep the pot small and ' +
              'let villain bluff into you.',
        streets: [
            { street: 'Flop', action: 'Bet small', size: '33% pot',
              why: 'Cheap denial against the many hands that missed this board.' },
            { street: 'Turn', action: 'Check', size: '\u2014',
              why: 'Caps the pot and hands villain the chance to bluff a street you were never getting value on.' },
            { street: 'River', action: 'Bet', size: '75% pot',
              why: 'Only if villain checked back the turn - by then worse pairs have stopped folding.' }
        ],
        failsWhen: 'Villain is passive and never bluffs the turn you checked. ' +
                   'Against those players the check costs you a value bet.'
    },
    {
        id: 'V3',
        name: 'The Lobster Pot Trap',
        kind: 'value',
        match: { position: ['IP', 'OOP'], role: ['aggressor'], texture: ['ultradry'], category: [1] },
        trigger: 'You hold a monster on a board almost nobody connects with',
        idea: 'On a board this dry, big bets fold out everything you beat. Keep ' +
              'the weak pairs in the pot cheaply, then charge them once at the ' +
              'end when they are committed and there are no cards left to fear.',
        streets: [
            { street: 'Flop', action: 'Bet', size: '50% pot',
              why: 'Builds a pot without threatening the weak pairs you want along for the ride.' },
            { street: 'Turn', action: 'Bet', size: '50% pot',
              why: 'Same size again. Nothing about this board should scare them off.' },
            { street: 'River', action: 'Over-bet', size: '100%+ pot',
              why: 'The trap closes. A player who called twice on a dry board is often priced in emotionally.' }
        ],
        failsWhen: 'The over-bet is the whole line. Against someone who folds ' +
                   'everything but the nuts to it, you built a pot for nothing.'
    },
    {
        id: 'V4',
        name: 'Check-Raise Value Spike',
        kind: 'value',
        match: { position: ['OOP'], role: ['caller'], texture: ['wet'], category: [1] },
        trigger: 'Villain bets the flop after you check',
        idea: 'Out of position with a big hand on a draw-heavy board, calling ' +
              'lets villain control the size and take free cards. Take the ' +
              'betting lead away immediately.',
        streets: [
            { street: 'Flop', action: 'Check-raise', size: '3.5\u00d7 their bet',
              why: 'Seizes the lead and makes every draw pay a bad price at once.' },
            { street: 'Turn', action: 'Bet', size: '75% pot',
              why: 'Keeps the pressure on rather than surrendering the initiative you just bought.' },
            { street: 'River', action: 'Bet', size: '75% pot',
              why: 'Value from the pairs and worse made hands that came along.' }
        ],
        failsWhen: 'A 3.5x check-raise is a large commitment out of position. ' +
                   'If villain only continues with better, this line loses a big pot instead of a small one.'
    },
    {
        id: 'V5',
        name: 'Probe Lead',
        kind: 'value',
        match: { position: ['OOP'], role: ['caller'], texture: ['wet', 'dry', 'ultradry'], category: [1, 2] },
        trigger: 'Villain checks back the flop, and the turn improves you',
        idea: 'A checked-back flop caps villain\u2019s range - strong hands almost ' +
              'always bet it. When the turn hits you, that weakness is yours to attack.',
        streets: [
            { street: 'Flop', action: 'Check-call', size: '\u2014',
              why: 'You have not made your hand yet; there is nothing to build a pot with.' },
            { street: 'Turn', action: 'Lead out', size: '66% pot',
              why: 'Villain showed weakness by checking. Now that you have equity, take the betting lead.' },
            { street: 'River', action: 'Bet', size: '75% pot',
              why: 'Value against the medium hands that called the turn.' }
        ],
        failsWhen: 'Some players check back strong hands to trap. Leading into ' +
                   'one of those turns your value bet into a bluff-catcher.'
    },
    {
        id: 'B1',
        name: 'Double Barrel Scare-Card',
        kind: 'bluff',
        match: { position: ['IP'], role: ['aggressor'], texture: ['wet'], category: [3] },
        trigger: 'The turn brings an Ace or King you can credibly represent',
        idea: 'You have a draw and a scare card arrived. You hold real equity if ' +
              'called, and a card villain has to respect if they are weak.',
        streets: [
            { street: 'Flop', action: 'Bet', size: '50% pot',
              why: 'Standard continuation bet with a hand that can improve.' },
            { street: 'Turn', action: 'Bet', size: '75% pot',
              why: 'The scare card does the work. Their medium pairs cannot continue comfortably.' },
            { street: 'River', action: 'Give up', size: '\u2014',
              why: 'If the draw missed, the story is over. A third barrel here is burning money.' }
        ],
        failsWhen: 'The give-up is not optional. Firing a third barrel because ' +
                   'the first two did not work is how this line loses stacks.'
    },
    {
        id: 'B2',
        name: 'Triple Barrel Bluff',
        kind: 'bluff',
        risk: 'high',
        match: { position: ['IP'], role: ['aggressor'], texture: ['wet'], category: [3] },
        trigger: 'Your draw bricks completely and the river is a blank',
        idea: 'The over-bet targets exactly one thing: the medium pairs that ' +
              'called two streets and cannot beat a large bet on a board where ' +
              'nothing got there.',
        streets: [
            { street: 'Flop', action: 'Bet', size: '50% pot',
              why: 'Continuation bet with equity behind it.' },
            { street: 'Turn', action: 'Bet', size: '50% pot',
              why: 'Smaller than the value line - keeps the pot manageable while the draw is still live.' },
            { street: 'River', action: 'Over-bet', size: '100% pot',
              why: 'A size their medium pairs cannot call. This only works against a player capable of folding.' }
        ],
        failsWhen: 'This is the highest-variance line in the playbook and the ' +
                   'one most dependent on villain being able to fold. Against a ' +
                   'calling station it is a pure donation, and against a strong ' +
                   'river range it is worse. Do not run it on a read you do not have.'
    },
    {
        id: 'B3',
        name: 'Delayed Turn Probe Raise',
        kind: 'bluff',
        match: { position: ['OOP'], role: ['caller'], texture: ['wet', 'dry', 'ultradry'], category: [3, 4] },
        trigger: 'Villain bets small on the flop, or checks back a capped turn',
        idea: 'Small bets and checked turns both signal a range that cannot ' +
              'take heat. Backdoor equity or an Ace blocker is enough to apply it.',
        streets: [
            { street: 'Flop', action: 'Check-call', size: '\u2014',
              why: 'Their small bet gives you a cheap price to continue with a weak holding.' },
            { street: 'Turn', action: 'Raise', size: '100% pot',
              why: 'Attacks a capped range at the point where villain has the least defence.' },
            { street: 'River', action: 'Give up', size: '\u2014',
              why: 'The bluff had one shot. If it did not work, stop.' }
        ],
        failsWhen: 'Small flop bets are not always weakness - some players size ' +
                   'down with strong hands precisely to induce this.'
    },
    {
        id: 'B4',
        name: 'Flop Check-Raise Semi-Bluff',
        kind: 'bluff',
        match: { position: ['OOP'], role: ['caller'], texture: ['wet'], category: [3] },
        trigger: 'Villain bets the flop and you hold a combo draw',
        idea: 'With a combo draw you often have more equity than the hand ' +
              'betting into you. Raising wins the pot now or leaves you plenty ' +
              'of outs when it does not.',
        streets: [
            { street: 'Flop', action: 'Check-raise', size: '3.5\u00d7 their bet',
              why: 'Maximum fold equity at the moment your hand equity is highest.' },
            { street: 'Turn', action: 'Bet', size: '75% pot',
              why: 'Follows through on the story and keeps the fold equity alive.' },
            { street: 'River', action: 'Give up', size: '\u2014',
              why: 'The draw missed and the pot is already large. Stop.' }
        ],
        failsWhen: 'Two large bets with a hand that is nothing if it misses. ' +
                   'The give-up on the river is what keeps this line survivable.'
    },
    {
        id: 'B5',
        name: 'Floating Delay Bluff',
        kind: 'bluff',
        match: { position: ['IP'], role: ['caller'], texture: ['dry', 'ultradry'], category: [3, 4] },
        trigger: 'You call the flop in position and villain checks the turn',
        idea: 'A continuation bet followed by a turn check is the clearest ' +
              'weakness pattern in poker. The float costs one bet to find it.',
        streets: [
            { street: 'Flop', action: 'Call', size: '\u2014',
              why: 'One cheap card in position to see whether their aggression continues.' },
            { street: 'Turn', action: 'Bet', size: '66% pot',
              why: 'They gave up on the pot. Take it.' },
            { street: 'River', action: 'Give up', size: '\u2014',
              why: 'If they called the turn, they have something. Move on.' }
        ],
        failsWhen: 'Some players check the turn intending to call down. The ' +
                   'float is cheap; the second barrel against those players is not.'
    }
];

// ---------------------------------------------------------------------------
// Fallbacks for the cells the ten lines do not reach.
//
// These are NOT part of the source framework. They exist so the funnel always
// terminates in an answer, and they are rendered with a DEFAULT badge and this
// disclaimer so they can never be mistaken for one of the ten researched
// lines. Keyed by hand category, which is what actually determines the
// fallback - with no archetype to follow, category alone decides whether you
// are betting, controlling, drawing or folding.
// ---------------------------------------------------------------------------

const PF_DEFAULT_DISCLAIMER =
    'The playbook has no named line for this exact spot. What follows is a ' +
    'general fallback, not one of the ten lines.';

const PF_DEFAULTS = {
    1: {
        id: 'D1',
        name: 'Value, no archetype',
        kind: 'value',
        idea: 'You have a strong hand and no named line covers this spot. Bet ' +
              'it, and size to the texture: bigger where draws exist, smaller ' +
              'where villain needs a reason to keep calling.',
        streets: [
            { street: 'Flop', action: 'Bet', size: '50-66% pot',
              why: 'Build the pot while you are ahead.' },
            { street: 'Turn', action: 'Bet', size: '66-75% pot',
              why: 'Keep charging unless the board has clearly turned against you.' },
            { street: 'River', action: 'Bet', size: '66-75% pot',
              why: 'Value from worse. Slow down only if the obvious draw completed.' }
        ],
        failsWhen: 'Generic advice. A named line, where one exists, will beat this.'
    },
    2: {
        id: 'D2',
        name: 'Showdown value, no archetype',
        kind: 'value',
        idea: 'Your hand wins a small pot and loses a big one. Get to showdown ' +
              'without inflating the pot.',
        streets: [
            { street: 'Flop', action: 'Check or bet small', size: '0-33% pot',
              why: 'Cheap denial at most. There is little worse that calls a large bet.' },
            { street: 'Turn', action: 'Check / call one bet', size: '\u2014',
              why: 'Pot control. You are bluff-catching, not value betting.' },
            { street: 'River', action: 'Check / call', size: '\u2014',
              why: 'Let them bluff. Betting here folds out everything you beat.' }
        ],
        failsWhen: 'Passive by design - against players who never bluff, this ' +
                   'line leaves value on the table.'
    },
    3: {
        id: 'D3',
        name: 'Draw, no archetype',
        kind: 'bluff',
        idea: 'You have equity but no named line. Either semi-bluff cheaply or ' +
              'take the free card - what you must not do is pay a big price to ' +
              'chase.',
        streets: [
            { street: 'Flop', action: 'Bet small or check', size: '0-33% pot',
              why: 'Cheap fold equity while your equity is highest.' },
            { street: 'Turn', action: 'Continue only if cheap', size: '\u2014',
              why: 'Pot odds decide this, not the story you want to tell.' },
            { street: 'River', action: 'Give up if missed', size: '\u2014',
              why: 'A busted draw with no plan is not a bluffing hand.' }
        ],
        failsWhen: 'Generic. B1-B5 are sharper wherever one of them applies.'
    },
    4: {
        id: 'D4',
        name: 'Air - check and fold',
        kind: 'bluff',
        idea: 'No pair, no draw, and no archetype that wants you bluffing here. ' +
              'This is the answer most players least want and most need: give ' +
              'up cheaply and keep the money for a spot with equity.',
        streets: [
            { street: 'Flop', action: 'Check / fold', size: '\u2014',
              why: 'Nothing to protect and nothing to draw to.' },
            { street: 'Turn', action: 'Check / fold', size: '\u2014',
              why: 'Barrelling without equity or a read is how stacks disappear.' },
            { street: 'River', action: 'Check / fold', size: '\u2014',
              why: 'Move on.' }
        ],
        failsWhen: 'Folding too much is exploitable in theory. In practice it ' +
                   'costs far less than the alternative this framework is not equipped to guide.'
    }
};

// ---------------------------------------------------------------------------
// The three mistakes the source called out by name. Rendered as warnings
// alongside whichever result the funnel produced, when the spot is one where
// the mistake actually happens. Advisory only - they flag a known trap, they
// do not score the player.
// ---------------------------------------------------------------------------

const PF_MISTAKES = [
    {
        id: 'M1',
        name: 'Fold isolation',
        applies: (c) => c.category === 2 && (c.texture === 'dry' || c.texture === 'ultradry'),
        text: 'Do not pot this board with a weak top pair. A large bet on a dry ' +
              'flop folds out every hand you beat and gets called only by hands ' +
              'that beat you - you isolate yourself against the top of their range.'
    },
    {
        id: 'M2',
        name: 'Over-building with medium value',
        applies: (c) => c.category === 2,
        text: 'Category 2 hands want a small pot. Every extra bet you put in ' +
              'moves this hand from comfortable showdown value towards an ' +
              'expensive bluff-catch.'
    },
    {
        id: 'M3',
        name: 'Third barrel into a strong range',
        applies: (c) => c.category === 3 || c.category === 4,
        text: 'When a bluff line says give up, give up. Villain\u2019s river range ' +
              'after calling two streets is strong and heavily weighted to hands ' +
              'that call again - a third barrel is not a bluff, it is a donation.'
    }
];

// ---------------------------------------------------------------------------
// Range-width modifier. See PF_RANGE_MODIFIERS_NOTE below for the rationale;
// this augments whichever line/fallback pfResolve() picks, it never changes
// which one gets picked.
// ---------------------------------------------------------------------------

const PF_TIGHT_OPENERS = new Set(['UTG', 'MP']);

function pfRangeWidth(position, role) {
    if (role === 'aggressor') {
        return PF_TIGHT_OPENERS.has(position) ? 'tight' : 'wide';
    }
    if (position === 'BB') return 'wide';
    return 'tight';
}

function computeRangeModifier(heroPos, heroRole, villainPos, villainRole) {
    if (!heroPos || !villainPos) return null;
    const heroWidth = pfRangeWidth(heroPos, heroRole);
    const villainWidth = pfRangeWidth(villainPos, villainRole);

    if (heroWidth === 'wide' && villainWidth === 'wide') {
        return { flag: 'both-wide', note:
            'Both ranges are wide and merged here (' + heroPos + ' vs ' + villainPos +
            '). Lean toward smaller, more frequent bets and thinner value - neither ' +
            'range is polarized enough to demand a big pot to protect it.' };
    }
    if (heroRole === 'aggressor' && heroWidth === 'tight' && villainWidth === 'wide') {
        return { flag: 'aggressor-tight', note:
            'Your range is narrow and strong for this pot (' + heroPos + ' opening) ' +
            'against a wide, capped defending range (' + villainPos + '). That range ' +
            'advantage supports betting bigger and more often than the texture alone ' +
            'would suggest, even on boards that would otherwise call for checking.' };
    }
    if (heroRole === 'caller' && heroWidth === 'wide' && villainWidth === 'tight') {
        return { flag: 'aggressor-tight', note:
            'Villain\u2019s range is narrow and strong for this pot (' + villainPos +
            ' opening) against your wider, capped defending range. Expect to face ' +
            'bigger, more frequent bets than the texture alone would suggest, and ' +
            'give up more readily against continued pressure.' };
    }
    if (heroRole === 'aggressor' && heroWidth === 'wide' && villainWidth === 'tight') {
        return { flag: 'aggressor-wide', note:
            'Villain\u2019s continuing range (' + villainPos + ') is narrower and ' +
            'stronger than usual for this pot type. Shade your frequency and sizing ' +
            'down from the pot-type default, and give up more readily against resistance.' };
    }
    if (heroRole === 'caller' && heroWidth === 'tight' && villainWidth === 'wide') {
        return { flag: 'aggressor-wide', note:
            'Your continuing range (' + heroPos + ') is narrower and stronger than ' +
            'usual for this pot type. Villain should be shading their frequency and ' +
            'sizing down against you - use that to continue a little wider than the ' +
            'base line suggests.' };
    }
    return { flag: 'both-tight', note:
        'Both ranges are narrow and strong here (' + heroPos + ' vs ' + villainPos +
        '). Expect a slower, more standard-sized game with less merged betting either way.' };
}

// ---------------------------------------------------------------------------
// Resolution
// ---------------------------------------------------------------------------

/** Does a line apply to this exact (position, role, texture, category) cell? */
function pfLineMatches(line, cell) {
    return line.match.position.includes(cell.position) &&
           line.match.role.includes(cell.role) &&
           line.match.texture.includes(cell.texture) &&
           line.match.category.includes(cell.category);
}

/**
 * Resolve a cell to the lines that apply. Returns { lines, fallback,
 * rangeModifier }. `rangeModifier` is advisory-only and present when the
 * cell carries heroPos/villainPos (set by the Study-mode bridge); it never
 * changes which line/fallback is selected.
 */
function pfResolve(cell) {
    const lines = POSTFLOP_LINES.filter((l) => pfLineMatches(l, cell));
    const rangeModifier = (cell.heroPos && cell.villainPos)
        ? computeRangeModifier(cell.heroPos, cell.role,
            cell.villainPos, cell.role === 'aggressor' ? 'caller' : 'aggressor')
        : null;
    return {
        lines,
        fallback: lines.length ? null : PF_DEFAULTS[cell.category],
        rangeModifier
    };
}

/** Warnings that apply to a cell, regardless of which line was chosen. */
function pfMistakesFor(cell) {
    return PF_MISTAKES.filter((m) => m.applies(cell));
}

/** Every cell in the space - used by the coverage test and the browse view. */
function pfAllCells() {
    const cells = [];
    for (const p of PF_POSITIONS) {
        for (const r of PF_ROLES) {
            for (const t of PF_TEXTURES) {
                for (const c of PF_CATEGORIES) {
                    cells.push({ position: p.id, role: r.id, texture: t.id, category: c.id });
                }
            }
        }
    }
    return cells;
}
