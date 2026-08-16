// GTO Preflop Trainer - multiway spot extension
//
// Adds two scenarios that were always present in the chart data but had no
// way to be addressed by the UI:
//
//   vs_OpenCall  "Facing an Open + a Caller"  (Hero can squeeze)
//   vs_3B_Cold   "Facing a 3-Bet (Not Yours)" (Hero cold 4-bets or folds)
//
// Why this exists as a separate file: findChartPath() builds filenames from a
// fixed (hero, villain) template, so it can only ever name heads-up nodes.
// Roughly half of the shipped chart files contain a third player and were
// unreachable. Rather than rewrite that template, this module treats the
// "villain" slot as an opaque token - for these two scenarios it carries a
// *line id* (the chart's filename stem) instead of a single position. Every
// existing helper that just forwards that token (loadChartFor, getLeafFreqs,
// step1AllFold, ...) then works unchanged.
//
// This file must load AFTER app.js and study.js.
//
// IMPORTANT - on the cold-3bet nodes: the upstream solve never contained
// "cold-call a 3-bet" as a legal action. Checked across all 1,476 upstream
// range files: 129 branches where someone calls an open, 24 where someone
// calls a squeeze, 0 where anyone cold-calls a 3-bet. So these charts offer
// Raise-or-Fold only. That is a property of the source solve, not a bug and
// not a rendering problem - see COLD_3B_NOTE below, which says so in the UI.
// Do not "fill in" a Call action here: the Raise/Fold frequencies were solved
// in a two-action tree, and renormalising them to make room for an invented
// Call would silently corrupt the numbers that are real.

(function () {
    'use strict';

    // -----------------------------------------------------------------------
    // The spots. Every entry is a chart filename stem that exists on disk.
    // -----------------------------------------------------------------------

    // Token meaning "no solved chart for this traffic - use the estimated
    // range from heuristic-ranges.js".
    const EST = 'estimated';

    // Hero faces an open plus a cold-call. The solve only ever modelled the
    // BTN as that caller, and only with Hero in a blind, so these six charts
    // are the whole of the solved coverage. Every other legal (opener, caller)
    // pair falls to EST - which is why CO and BTN get only that entry.
    //
    // The alternative was to enumerate all 20 legal pairs, but the 14 with no
    // chart would each return the identical estimated range for their seat, so
    // ten indistinguishable BB buttons would mislead more than one honest
    // catch-all does.
    const SQUEEZE_LINES = {
        CO: [EST],
        BTN: [EST],
        SB: ['UTG_2.5bb_BTN_Call_SB', 'MP_2.5bb_BTN_Call_SB', 'CO_2.5bb_BTN_Call_SB', EST],
        BB: ['UTG_2.5bb_BTN_Call_BB', 'MP_2.5bb_BTN_Call_BB', 'CO_2.5bb_BTN_Call_BB', EST]
    };

    // Someone opened, someone else 3-bet, and Hero has not acted yet.
    const COLD_3B_LINES = {
        UTG: [],
        MP: [],
        CO: ['UTG_2.5bb_MP_8.5bb_CO'],
        BTN: ['UTG_2.5bb_MP_8.5bb_BTN', 'UTG_2.5bb_CO_8.5bb_BTN', 'MP_2.5bb_CO_8.5bb_BTN'],
        SB: ['UTG_2.5bb_MP_8.5bb_SB', 'UTG_2.5bb_CO_8.5bb_SB', 'UTG_2.5bb_BTN_8.5bb_SB',
             'MP_2.5bb_CO_8.5bb_SB', 'MP_2.5bb_BTN_8.5bb_SB', 'CO_2.5bb_BTN_8.5bb_SB'],
        BB: ['UTG_2.5bb_MP_8.5bb_BB', 'UTG_2.5bb_CO_8.5bb_BB', 'UTG_2.5bb_BTN_8.5bb_BB',
             'UTG_2.5bb_SB_11.0bb_BB', 'MP_2.5bb_CO_8.5bb_BB', 'MP_2.5bb_BTN_8.5bb_BB',
             'MP_2.5bb_SB_11.0bb_BB', 'CO_2.5bb_BTN_8.5bb_BB', 'CO_2.5bb_SB_11.0bb_BB',
             'BTN_2.5bb_SB_11.0bb_BB']
    };

    const MW = {
        vs_OpenCall: { lines: SQUEEZE_LINES, dir: 'vs_Open' },
        vs_3B_Cold: { lines: COLD_3B_LINES, dir: 'vs_3B' }
    };

    // Shown when a loaded chart turns out to have no calling action at all.
    // The cold-3bet wording states a fact that was verified directly against
    // the upstream solve (0 cold-call branches in 1,476 files). The generic
    // wording deliberately does NOT claim to know why the action is absent,
    // because that was not verified for those nodes - e.g. the three SB
    // squeeze charts are also raise-or-fold, and it was not established
    // whether flatting was excluded from the tree or simply solved to zero.
    const COLD_3B_NOTE =
        'This chart set solves this spot as 4-bet or fold. Cold-calling a 3-bet ' +
        'was not a legal action anywhere in the source solve, so there is no ' +
        'calling frequency to show here - not because flatting is never correct, ' +
        'but because this solve never priced it.';

    const NO_CALL_NOTE =
        'This chart offers raise or fold only - the source solve provides no ' +
        'calling frequency for this spot, so none is shown.';

    // Attached to solved squeeze results: the six charts all have a BTN caller.
    const SQUEEZE_SCOPE_NOTE =
        'This solve only models the BTN as the cold-caller. If your caller sat ' +
        'elsewhere, this is the closest chart, not an exact one - and an earlier ' +
        'caller (with more players still behind you) both calls tighter and ' +
        'leaves more hands left to act, so squeeze somewhat less than shown.';

    // Attached to every estimated result. First line states the tier; the
    // second states the limitation most likely to mislead - one range per seat
    // standing in for every opener, when the solved charts show the opener
    // moves the answer a long way (BB raises 6.3% vs UTG, 10.1% vs CO).
    const HEURISTIC_NOTE =
        'These numbers are NOT solver output. The source solve has no chart for ' +
        'this seat facing an open plus a caller, so this is a hand-specified ' +
        'estimate, calibrated against the six solved open-plus-caller charts.';

    const OPENER_AGNOSTIC_NOTE =
        'This estimate reads the same whoever opened, which the solved charts ' +
        'say is a simplification - tighten it against an early opener, widen it ' +
        'against a late one. Each hand does one thing where a real chart would ' +
        'mix, so there is nothing to randomise and the dice roll is hidden.';

    // Shown above the line list, before a choice is made.
    const PICKER_NOTES = {
        vs_OpenCall:
            'Lines marked SOLVED come from the solver and cover a BTN caller ' +
            'only. If your traffic is not listed, the ESTIMATED entry covers ' +
            'it - or pick a solved line with the same OPENER, whose range ' +
            "matters more than the caller's seat.",
        vs_3B_Cold:
            'Only these exact lines were solved. If your seats are not listed, ' +
            'pick the line with the same OPENER and the closest 3-bettor.'
    };

    function actionNamesOf(chartData) {
        try {
            const r = chartData && chartData.strategy && chartData.strategy.upi_ranges;
            return r ? Object.keys(r) : null;
        } catch (e) { return null; }
    }

    function isMultiway(scenario) {
        return Object.prototype.hasOwnProperty.call(MW, scenario);
    }

    function linesFor(hero, scenario) {
        if (!isMultiway(scenario)) return [];
        return (MW[scenario].lines[hero] || []).slice();
    }

    // -----------------------------------------------------------------------
    // Turn a filename stem into something a human can read.
    //   UTG_2.5bb_BTN_Call_SB    -> "UTG opens 2.5bb, BTN calls"
    //   UTG_2.5bb_MP_8.5bb_BTN   -> "UTG opens 2.5bb, MP 3-bets 8.5bb"
    // -----------------------------------------------------------------------
    function describeLine(lineId) {
        if (lineId === EST) return 'Any other opener / caller';
        if (typeof lineId !== 'string') return String(lineId);
        const t = lineId.split('_');
        if (t.length < 5) return lineId;
        const opener = t[0];
        const openSize = t[1];
        if (t[3] === 'Call') return `${opener} opens ${openSize}, ${t[2]} calls`;
        return `${opener} opens ${openSize}, ${t[2]} 3-bets ${t[3]}`;
    }

    // -----------------------------------------------------------------------
    // Register the scenarios. SCENARIOS/SCENARIO_LABELS are `const`, but these
    // are mutations rather than rebindings, so they are legal.
    // -----------------------------------------------------------------------

    SCENARIO_LABELS.vs_OpenCall = 'Facing an Open + a Caller';
    SCENARIO_SUBLABELS.vs_OpenCall = 'A raise and a cold-call in front of Hero';
    SCENARIO_LABELS.vs_3B_Cold = 'Facing a 3-Bet (Not Yours)';
    SCENARIO_SUBLABELS.vs_3B_Cold = 'Someone opened, someone else 3-bet, Hero has not acted';

    // Slot each one next to the scenario it most resembles, rather than
    // appending both to the end.
    if (SCENARIOS.indexOf('vs_OpenCall') === -1) {
        const i = SCENARIOS.indexOf('vs_Open');
        SCENARIOS.splice(i === -1 ? SCENARIOS.length : i + 1, 0, 'vs_OpenCall');
    }
    if (SCENARIOS.indexOf('vs_3B_Cold') === -1) {
        const i = SCENARIOS.indexOf('vs_3B');
        SCENARIOS.splice(i === -1 ? SCENARIOS.length : i + 1, 0, 'vs_3B_Cold');
    }

    // -----------------------------------------------------------------------
    // Patch the resolution helpers. Each one delegates to the original for
    // every pre-existing scenario, so heads-up behaviour is untouched.
    // -----------------------------------------------------------------------

    const origFindChartPath = findChartPath;
    findChartPath = function (hero, villain, scenario) {
        if (isMultiway(scenario)) {
            if (!hero || !villain) return null;
            if (linesFor(hero, scenario).indexOf(villain) === -1) return null;
            // The estimated line has no file behind it; loadChartFor below
            // intercepts before this is ever consulted for it.
            if (villain === EST) return null;
            return `data/${MW[scenario].dir}/${hero}/${villain}.json`;
        }
        return origFindChartPath(hero, villain, scenario);
    };

    // The estimated line is synthesised rather than fetched. It comes back
    // shaped exactly like a solved chart, so every downstream consumer -
    // computeFreqsForHand, showResult, the breakdown rows - needs no special
    // case; only the badge and the notes key off __heuristic.
    const origLoadChartFor = loadChartFor;
    loadChartFor = async function (hero, villain, scenario) {
        if (isMultiway(scenario) && villain === EST) {
            if (typeof buildHeuristicChart !== 'function') return null;
            return buildHeuristicChart(hero);
        }
        return origLoadChartFor(hero, villain, scenario);
    };

    const origIsScenarioLegalForHero = isScenarioLegalForHero;
    isScenarioLegalForHero = function (hero, scenario) {
        if (isMultiway(scenario)) return linesFor(hero, scenario).length > 0;
        return origIsScenarioLegalForHero(hero, scenario);
    };

    // Hero has not put money in yet in either of these spots, so there is no
    // earlier action of Hero's that could make them unreachable. (The original
    // assumes Hero opened for vs_3B, which would reject every cold spot.)
    const origIsReachable = isReachable;
    isReachable = async function (hero, villain, scenario, hand) {
        if (isMultiway(scenario)) return true;
        return origIsReachable(hero, villain, scenario, hand);
    };

    const origReachableVillains = reachableVillains;
    reachableVillains = async function (hero, scenario, hand) {
        if (isMultiway(scenario)) return linesFor(hero, scenario);
        return origReachableVillains(hero, scenario, hand);
    };

    // -----------------------------------------------------------------------
    // Presentation
    // -----------------------------------------------------------------------

    // A short scope note above the line list, so the coverage limit is visible
    // BEFORE a choice is made rather than only after clicking through.
    let pickerNoteEl = null;
    function ensurePickerNoteEl() {
        if (pickerNoteEl) return pickerNoteEl;
        const container = document.getElementById('study-villain-buttons');
        if (!container || !container.parentNode) return null;
        pickerNoteEl = document.createElement('p');
        pickerNoteEl.id = 'multiway-picker-note';
        pickerNoteEl.className = 'result-tree-note';
        pickerNoteEl.hidden = true;
        container.parentNode.insertBefore(pickerNoteEl, container);
        return pickerNoteEl;
    }

    const origRenderVillainButtons = renderVillainButtons;
    renderVillainButtons = function (villains) {
        const note = ensurePickerNoteEl();

        if (!isMultiway(studyScenario)) {
            if (note) note.hidden = true;
            return origRenderVillainButtons(villains);
        }

        const container = document.getElementById('study-villain-buttons');
        if (!container) return origRenderVillainButtons(villains);
        container.innerHTML = '';
        for (const lineId of villains) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'choice-btn';
            // Tier is visible before the click, not discovered after it.
            const label = document.createElement('span');
            label.textContent = describeLine(lineId);
            btn.appendChild(label);

            const badge = document.createElement('span');
            badge.className = lineId === EST
                ? 'mw-badge mw-badge-est'
                : 'mw-badge mw-badge-solved';
            badge.textContent = lineId === EST ? 'ESTIMATED' : 'SOLVED';
            btn.appendChild(badge);

            btn.addEventListener('click', () => selectVillain(lineId));
            container.appendChild(btn);
        }

        if (note) {
            note.textContent = PICKER_NOTES[studyScenario] || '';
            note.hidden = !note.textContent;
        }
    };

    // The breadcrumb would otherwise show a raw filename stem.
    const origUpdateBadges = updateBadges;
    updateBadges = function () {
        origUpdateBadges();
        try {
            if (isMultiway(studyScenario) && studyVillain && crumbVillainEl) {
                const label = describeLine(studyVillain);
                if (crumbVillainEl.textContent) crumbVillainEl.textContent = label;
            }
        } catch (e) { /* breadcrumb is cosmetic - never let it break navigation */ }
    };

    // Caveats attached to a multiway result: a missing action, a coverage
    // limit, or both. Rendered as a stack so several can apply at once.
    let noteEl = null;
    function ensureNoteEl() {
        if (noteEl) return noteEl;
        if (typeof resultBreakdownEl === 'undefined' || !resultBreakdownEl) return null;
        noteEl = document.createElement('div');
        noteEl.id = 'multiway-tree-note';
        noteEl.hidden = true;
        resultBreakdownEl.insertAdjacentElement('afterend', noteEl);
        return noteEl;
    }

    function renderNotes(el, notes) {
        el.innerHTML = '';
        for (const text of notes) {
            const p = document.createElement('p');
            p.className = 'result-tree-note';
            p.textContent = text;      // static strings only, never user input
            el.appendChild(p);
        }
        el.hidden = notes.length === 0;
    }

    const origShowResult = showResult;
    showResult = function (opts) {
        origShowResult(opts);
        try {
            const el = ensureNoteEl();
            if (!el) return;

            const forced = opts && opts.forcedFold;
            const acts = actionNamesOf(opts && opts.chartData);
            const notes = [];

            const heuristic = !!(opts && opts.chartData && opts.chartData.__heuristic);

            if (isMultiway(studyScenario) && !forced && acts) {
                if (heuristic) {
                    // Never claim the solve is silent here - it was never
                    // consulted. These two notes replace the solved-chart
                    // caveats entirely rather than stacking with them.
                    notes.push(HEURISTIC_NOTE, OPENER_AGNOSTIC_NOTE);
                } else {
                    // Drive the missing-action note off the chart that actually
                    // loaded rather than off the scenario name: the SB squeeze
                    // charts are raise-or-fold too, so keying on 'vs_3B_Cold'
                    // alone would leave those unexplained.
                    if (!acts.some((a) => /call/i.test(a))) {
                        notes.push(studyScenario === 'vs_3B_Cold' ? COLD_3B_NOTE : NO_CALL_NOTE);
                    }
                    // The coverage caveat applies to every squeeze chart,
                    // including the BB ones that do offer a Call.
                    if (studyScenario === 'vs_OpenCall') notes.push(SQUEEZE_SCOPE_NOTE);
                }
            }

            // Pure ranges have nothing to randomise: a die that always lands
            // on the same face would imply a precision these ranges lack.
            if (typeof diceWidgetEl !== 'undefined' && diceWidgetEl && heuristic) {
                diceWidgetEl.hidden = true;
                if (typeof diceRollBtn !== 'undefined' && diceRollBtn) diceRollBtn.hidden = true;
            }

            renderNotes(el, notes);
        } catch (e) { /* the note is advisory - never let it break the result */ }
    };
})();
