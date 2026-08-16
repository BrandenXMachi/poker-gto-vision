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

    // Hero is in a blind, someone opened, BTN flat-called. Hero may squeeze.
    const SQUEEZE_LINES = {
        SB: ['UTG_2.5bb_BTN_Call_SB', 'MP_2.5bb_BTN_Call_SB', 'CO_2.5bb_BTN_Call_SB'],
        BB: ['UTG_2.5bb_BTN_Call_BB', 'MP_2.5bb_BTN_Call_BB', 'CO_2.5bb_BTN_Call_BB']
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

    // The solve only ever modelled the BTN as the cold-caller of an open:
    // upstream contains exactly 6 nodes of the shape OPENER_2.5bb_CALLER_Call_HERO
    // and the caller is BTN in all 6. A player whose actual caller sat in a
    // different seat has no exact chart, so say what to substitute and which
    // way the substitution errs.
    const SQUEEZE_SCOPE_NOTE =
        'This solve only models the BTN as the cold-caller. If your caller sat ' +
        'elsewhere, this is the closest chart, not an exact one - and an earlier ' +
        'caller (with more players still behind you) both calls tighter and ' +
        'leaves more hands left to act, so squeeze somewhat less than shown.';

    // Shown above the line list, before a choice is made.
    const PICKER_NOTES = {
        vs_OpenCall:
            'This solve only modelled the BTN as the cold-caller. If your caller ' +
            'was in another seat, pick the line with the same OPENER - the ' +
            "opener's range matters far more than the caller's seat.",
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

    SCENARIO_LABELS.vs_OpenCall = 'Facing an Open + a BTN Caller';
    SCENARIO_SUBLABELS.vs_OpenCall = 'A raise and a BTN cold-call in front of Hero';
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
            return `data/${MW[scenario].dir}/${hero}/${villain}.json`;
        }
        return origFindChartPath(hero, villain, scenario);
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
            btn.textContent = describeLine(lineId);
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

            if (isMultiway(studyScenario) && !forced && acts) {
                // Drive the missing-action note off the chart that actually
                // loaded rather than off the scenario name: the SB squeeze
                // charts are raise-or-fold too, so keying on 'vs_3B_Cold'
                // alone would leave those unexplained.
                if (!acts.some((a) => /call/i.test(a))) {
                    notes.push(studyScenario === 'vs_3B_Cold' ? COLD_3B_NOTE : NO_CALL_NOTE);
                }
                // The coverage caveat applies to every squeeze chart, including
                // the BB ones that do offer a Call.
                if (studyScenario === 'vs_OpenCall') notes.push(SQUEEZE_SCOPE_NOTE);
            }

            renderNotes(el, notes);
        } catch (e) { /* the note is advisory - never let it break the result */ }
    };
})();
