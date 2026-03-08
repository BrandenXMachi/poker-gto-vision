"""
Flop Logic Engine - Rush & Cash GTO Decision System
Pure Python deterministic engine for flop decisions.

Six metrics: HPS, BWS, RAS, NAS, ERF, EFE
Two pipelines: Offensive (hero acts first) and Defensive (hero faces bet)
"""

import logging
from typing import Dict, Any, List, Tuple
from collections import Counter

from hand_evaluator import evaluate_hand, HandEvaluation, Card

# Import preflop ranges for RAS/NAS computation
from preflop_gto_analyzer import OPENING_RANGES, CALLING_VS_OPEN

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

RANK_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "Jack": 11, "Queen": 12, "King": 13, "Ace": 14
}

# C-bet frequencies (IP/OOP × pot type)
CBET_FREQ = {
    ("IP",  "open_raise"): 0.65,
    ("OOP", "open_raise"): 0.45,
    ("IP",  "3bet"):       0.70,
    ("OOP", "3bet"):       0.55,
    ("IP",  "4bet"):       0.70,
    ("OOP", "4bet"):       0.60,
}

# Base fold rates for Rush & Cash by pot type
BASE_FOLD_RATE = {
    "open_raise": 0.32,
    "3bet":       0.25,
    "4bet":       0.20,
}

# Action score weights
WEIGHTS = {
    "hand_power":    1.5,
    "range_adv":     2.0,
    "nut_adv":       2.0,
    "board_wetness": 0.3,   # wet board → slight penalty on large bets
    "fold_bonus":    0.9,
    "position":      1.0,   # IP bonus
    "bluff":         2.0,   # activated only when outs >= 6
}

# Bet size labels and pot fractions
BET_SIZES = [
    ("BET_SMALL",  0.25),
    ("BET_MEDIUM", 0.50),
    ("BET_LARGE",  0.80),
]


# ─────────────────────────────────────────────
#  HELPER — parse board card ranks
# ─────────────────────────────────────────────

def _parse_card_rank(card_str: str) -> int:
    """Extract numeric rank from 'Ace of Spades' style string."""
    parts = card_str.split(" of ")
    rank_str = parts[0].strip()
    return RANK_VALUES.get(rank_str, 0)


def _parse_board_ranks(board_cards: List[str]) -> List[int]:
    """Return sorted board ranks descending."""
    ranks = [_parse_card_rank(c) for c in board_cards]
    return sorted(ranks, reverse=True)


# ─────────────────────────────────────────────
#  METRIC A — Hand Power Score (HPS)
# ─────────────────────────────────────────────

def compute_hps(hero_cards: List[str], board_cards: List[str],
                hand_eval: HandEvaluation) -> Tuple[float, str]:
    """
    Compute Hand Power Score.

    Returns (hps, pair_subtype) where pair_subtype is one of:
    "overpair", "tptk", "top_pair_weak", "middle_pair", "bottom_pair", "none"
    """
    hps = 0.0
    pair_subtype = "none"

    board_ranks = _parse_board_ranks(board_cards)   # [highest, ..., lowest]
    hero_ranks  = sorted([_parse_card_rank(c) for c in hero_cards], reverse=True)

    made = hand_eval.made_hand

    # ── Made hand base score ─────────────────
    if made == "high_card":
        hps = 0.0

    elif made == "pair":
        pair_rank = hand_eval.made_hand_rank - 100

        if hand_eval.has_pocket_pair:
            # Pocket pair — is it an overpair?
            if pair_rank > board_ranks[0]:
                pair_subtype = "overpair"
                hps = 5.0
            else:
                # Pocket pair that's not an overpair
                pair_subtype = "middle_pair"
                hps = 3.5
        else:
            # Paired with a board card — classify by which board card
            if board_ranks and pair_rank == board_ranks[0]:
                # Paired top board card — TPTK or top pair weak?
                # Kicker = highest hero card that's NOT the paired card
                kicker = max([r for r in hero_ranks if r != pair_rank], default=0)
                if kicker >= 12:    # Queen or better kicker
                    pair_subtype = "tptk"
                    hps = 4.5
                else:
                    pair_subtype = "top_pair_weak"
                    hps = 3.5
            elif len(board_ranks) >= 2 and pair_rank == board_ranks[1]:
                pair_subtype = "middle_pair"
                hps = 3.0
            else:
                pair_subtype = "bottom_pair"
                hps = 2.0

    elif made == "two_pair":
        hps = 6.0
    elif made == "trips":
        hps = 8.0   # Sets are near-unbeatable on flop
    elif made == "straight":
        hps = 6.5
    elif made == "flush":
        hps = 7.5
    elif made == "full_house":
        hps = 9.0
    elif made == "quads":
        hps = 10.0
    elif made == "straight_flush":
        hps = 10.0

    # ── Draw bonuses ─────────────────────────
    if hand_eval.is_combo_draw:
        hps += 3.0   # Flush + straight = massive equity
    else:
        if hand_eval.has_flush_draw:
            hps += 2.0
        if hand_eval.has_oesd:
            hps += 2.0
        elif hand_eval.has_gutshot:
            hps += 1.0
        if hand_eval.has_backdoor_flush_draw:
            hps += 0.5
        if hand_eval.has_backdoor_straight_draw:
            hps += 0.5

    # ── Overcard bonus ───────────────────────
    if made in ("high_card", None) or made == "pair":
        # Count hero cards that are OVER the highest board card
        overcards = sum(1 for r in hero_ranks if r > board_ranks[0]) if board_ranks else 0
        hps += min(overcards * 0.5, 1.0)

    # ── Kicker bonus ─────────────────────────
    # Only relevant when we have exactly one pair
    if made == "pair" and hand_eval.kickers:
        top_kicker = hand_eval.kickers[0]
        if top_kicker == 14:    # Ace kicker
            hps += 1.0
        elif top_kicker == 13:  # King kicker
            hps += 0.5

    logger.debug(f"HPS={hps:.2f}, pair_subtype={pair_subtype}, made={made}")
    return hps, pair_subtype


# ─────────────────────────────────────────────
#  METRIC B — Board Wetness Score (BWS)
# ─────────────────────────────────────────────

def compute_bws(board_cards: List[str]) -> float:
    """
    Compute Board Wetness Score.
    1-2 = dry, 3-4 = semi-wet, 5-6 = wet
    """
    if len(board_cards) != 3:
        return 1.0

    try:
        cards = [Card(c) for c in board_cards]
    except Exception:
        return 2.0

    ranks  = sorted([c.rank for c in cards], reverse=True)
    suits  = [c.suit for c in cards]
    bws    = 1.0  # base

    # ── Suitedness ───────────────────────────
    suit_counts = Counter(suits)
    max_suit    = max(suit_counts.values())
    if max_suit == 3:
        bws += 3.0   # Monotone board — flush draw for anyone with 1 card of that suit
    elif max_suit == 2:
        bws += 2.0   # Two-tone — flush draw possible

    # ── Connectivity (count connected pairs in the 3 cards) ──
    connected_pairs = 0
    for i in range(len(ranks)):
        for j in range(i + 1, len(ranks)):
            gap = ranks[i] - ranks[j]
            if gap == 1:
                connected_pairs += 1
    if connected_pairs >= 2:
        bws += 2.0
    elif connected_pairs == 1:
        bws += 1.0

    # Wheel connectivity bonus (A-2-3, A-3-4, A-2-4)
    if 14 in ranks and any(r <= 5 for r in ranks):
        bws += 0.5

    # ── Paired board — REDUCES wetness ───────
    rank_counts = Counter(ranks)
    max_rank_count = max(rank_counts.values())
    if max_rank_count == 3:
        bws -= 2.0   # Trips on board → very dry
    elif max_rank_count == 2:
        bws -= 1.0   # Paired board → reduces straight/flush danger

    bws = max(1.0, min(6.0, bws))
    logger.debug(f"BWS={bws:.2f}")
    return bws


# ─────────────────────────────────────────────
#  HELPERS for RAS / NAS
# ─────────────────────────────────────────────

def _get_range_for_position(position: str, villain_position: str = None) -> List[str]:
    """
    Return the appropriate preflop range for a given position.
    If villain_position provided, return the calling range vs that villain.
    Otherwise return opening range.
    """
    if villain_position:
        key = f"{position}_vs_{villain_position}"
        if key in CALLING_VS_OPEN:
            return CALLING_VS_OPEN[key]
    # Fall back to opening range
    return OPENING_RANGES.get(position, OPENING_RANGES["BTN"])


def _hand_notation_hits_board(hand_notation: str, board_ranks: List[int]) -> int:
    """
    Returns a hit score for a hand notation vs board ranks.
    0 = no hit, 1 = pair on board, 2 = two pair / set possible

    Hand notation: "AKs", "QQ", "T9s", etc.
    """
    if len(hand_notation) < 2:
        return 0

    rank_char_map = {
        'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
        '9': 9,  '8': 8,  '7': 7,  '6': 6,  '5': 5,
        '4': 4,  '3': 3,  '2': 2
    }

    r1_char = hand_notation[0].upper()
    r2_char = hand_notation[1].upper()
    r1 = rank_char_map.get(r1_char, 0)
    r2 = rank_char_map.get(r2_char, 0)

    hits = 0
    if r1 in board_ranks:
        hits += 1
    if r2 in board_ranks:
        hits += 1

    # Pocket pair hitting a board card = set
    if r1 == r2 and r1 in board_ranks:
        return 2  # Set

    return hits


def _count_nut_combos(hand_range: List[str], board_ranks: List[int]) -> int:
    """
    Count how many hands in the range make nutty hands (sets, straights, flushes, top two pair).
    Simplified heuristic — counts 2-hit hands and pocket pairs that hit board.
    """
    nuts = 0
    for hand in hand_range:
        score = _hand_notation_hits_board(hand, board_ranks)
        if score == 2:
            nuts += 1
    return nuts


def _count_range_strength(hand_range: List[str], board_ranks: List[int]) -> float:
    """Weighted sum of how well a range connects with the board."""
    if not hand_range:
        return 0.0
    total = 0.0
    for hand in hand_range:
        score = _hand_notation_hits_board(hand, board_ranks)
        total += score * 1.5 if score == 2 else score
    return total / len(hand_range)


# ─────────────────────────────────────────────
#  METRIC C — Range Advantage Score (RAS)
# ─────────────────────────────────────────────

def compute_ras(hero_position: str, villain_position: str,
                board_cards: List[str]) -> Tuple[float, str]:
    """
    Compute Range Advantage Score.
    Returns (ras_numeric, ras_label)
    ras_numeric: positive = hero advantage, negative = villain advantage
    """
    board_ranks = _parse_board_ranks(board_cards)

    # Hero range (determined by position as caller or opener)
    hero_range    = _get_range_for_position(hero_position, villain_position)
    villain_range = _get_range_for_position(villain_position)

    hero_strength    = _count_range_strength(hero_range,    board_ranks)
    villain_strength = _count_range_strength(villain_range, board_ranks)

    ras = hero_strength - villain_strength

    if ras >= 1.0:
        label = "HERO_STRONG"
    elif ras >= 0.3:
        label = "HERO_SLIGHT"
    elif ras >= -0.3:
        label = "NEUTRAL"
    elif ras >= -1.0:
        label = "VILLAIN_SLIGHT"
    else:
        label = "VILLAIN_STRONG"

    logger.debug(f"RAS={ras:.3f} ({label})")
    return ras, label


# ─────────────────────────────────────────────
#  METRIC D — Nut Advantage Score (NAS)
# ─────────────────────────────────────────────

def compute_nas(hero_position: str, villain_position: str,
                board_cards: List[str]) -> Tuple[float, str]:
    """
    Compute Nut Advantage Score.
    Counts sets / two-pair combos per range.
    Returns (nas_numeric, nas_label)
    """
    board_ranks = _parse_board_ranks(board_cards)

    hero_range    = _get_range_for_position(hero_position, villain_position)
    villain_range = _get_range_for_position(villain_position)

    hero_nuts    = _count_nut_combos(hero_range,    board_ranks)
    villain_nuts = _count_nut_combos(villain_range, board_ranks)

    nas_raw = hero_nuts - villain_nuts

    # Normalise to -3 to +3 range
    total = max(hero_nuts + villain_nuts, 1)
    nas   = (nas_raw / total) * 3.0

    if nas >= 2.0:
        label = "HERO_STRONG"
    elif nas >= 0.5:
        label = "HERO_SLIGHT"
    elif nas >= -0.5:
        label = "NEUTRAL"
    elif nas >= -2.0:
        label = "VILLAIN_SLIGHT"
    else:
        label = "VILLAIN_STRONG"

    logger.debug(f"NAS={nas:.3f} ({label})")
    return nas, label


# ─────────────────────────────────────────────
#  METRIC E — Equity Realization Factor (ERF)
# ─────────────────────────────────────────────

def compute_erf(hand_eval: HandEvaluation, is_ip: bool,
                bws: float, pair_subtype: str) -> float:
    """
    Compute Equity Realization Factor.
    Multiplicative — applied to HPS to get effective_hps.
    """
    erf = 1.0

    # Position
    erf *= 1.05 if is_ip else 0.90

    # Draw type
    if hand_eval.is_combo_draw:
        erf *= 1.10
    elif hand_eval.has_flush_draw:
        erf *= 1.00
    elif hand_eval.has_oesd:
        erf *= 1.00
    elif hand_eval.has_gutshot:
        erf *= 0.90
    elif hand_eval.has_backdoor_flush_draw or hand_eval.has_backdoor_straight_draw:
        erf *= 0.85

    # Hand visibility — face-up hands on dry boards lose realization
    if pair_subtype == "tptk" and bws <= 2.0:
        erf *= 0.92   # TPTK is obvious on dry boards
    elif hand_eval.made_hand == "trips":
        erf *= 1.05   # Sets are disguised
    elif pair_subtype in ("bottom_pair", "middle_pair"):
        erf *= 0.88   # Marginal pairs lose a lot vs aggression

    # Board volatility
    if bws <= 2.0:
        erf *= 1.00
    elif bws <= 4.0:
        erf *= 0.92
    else:
        erf *= 0.80

    erf = max(0.50, min(1.20, erf))
    logger.debug(f"ERF={erf:.3f}")
    return erf


# ─────────────────────────────────────────────
#  METRIC F — Expected Fold Equity (EFE)
# ─────────────────────────────────────────────

def compute_efe(pot_size: float, bet_fraction: float,
                bws: float, ras: float,
                preflop_pot_type: str) -> Tuple[float, float]:
    """
    Compute Expected Fold Equity.
    Returns (fold_probability, fold_bonus_dollars)
    """
    base = BASE_FOLD_RATE.get(preflop_pot_type, 0.32)

    # Dry boards → more fold pressure
    board_pressure = (3.0 - bws) * 0.04
    board_pressure = max(-0.06, min(0.08, board_pressure))

    # Range advantage → more folds if hero is favored
    ras_factor = ras * 0.05
    ras_factor = max(-0.06, min(0.08, ras_factor))

    # Bet size factor
    if bet_fraction <= 0.30:
        bet_size_factor = 0.0
    elif bet_fraction <= 0.55:
        bet_size_factor = 0.05
    else:
        bet_size_factor = 0.10

    fold_prob = base + board_pressure + ras_factor + bet_size_factor
    fold_prob = max(0.05, min(0.75, fold_prob))

    fold_bonus = fold_prob * pot_size
    logger.debug(f"EFE: fold_prob={fold_prob:.3f}, fold_bonus=${fold_bonus:.2f}")
    return fold_prob, fold_bonus


# ─────────────────────────────────────────────
#  MINIMUM DEFENSE FREQUENCY
# ─────────────────────────────────────────────

def compute_mdf(pot_size: float, call_amount: float) -> float:
    """MDF = pot / (pot + bet)"""
    if call_amount <= 0:
        return 1.0
    return pot_size / (pot_size + call_amount)


# ─────────────────────────────────────────────
#  ACTION SCORE
# ─────────────────────────────────────────────

def _bet_size_penalty(effective_hps: float, bet_fraction: float) -> float:
    """Penalise large bets when hand is weak."""
    if effective_hps >= 6.0:
        return 0.0   # Strong hand — no penalty
    if bet_fraction >= 0.75:
        return (6.0 - effective_hps) * 0.8
    if bet_fraction >= 0.45:
        return (6.0 - effective_hps) * 0.3
    return 0.0


def compute_action_score(effective_hps: float, ras: float, nas: float,
                         bws: float, fold_bonus: float, is_ip: bool,
                         has_bluff_eligible_draw: bool,
                         bet_fraction: float) -> float:
    """Compute offensive action score for a given bet size."""

    bluff_bonus = WEIGHTS["bluff"] if has_bluff_eligible_draw else 0.0
    positional  = WEIGHTS["position"] if is_ip else 0.0
    penalty     = _bet_size_penalty(effective_hps, bet_fraction)

    score = (
        effective_hps      * WEIGHTS["hand_power"]
        + ras              * WEIGHTS["range_adv"]
        + nas              * WEIGHTS["nut_adv"]
        - bws              * WEIGHTS["board_wetness"]
        + fold_bonus       * WEIGHTS["fold_bonus"]
        + positional
        + bluff_bonus
        - penalty
    )
    return score


def compute_check_score(effective_hps: float, bws: float, is_ip: bool) -> float:
    """Check/trap score — favoured by strong hands and wet boards."""
    trap_bonus = 1.5 if effective_hps >= 8.0 else 0.0   # Trap with monsters
    return effective_hps * 0.8 + bws * 0.5 + trap_bonus


# ─────────────────────────────────────────────
#  OFFENSIVE PIPELINE
# ─────────────────────────────────────────────

def make_offensive_decision(
    effective_hps: float, ras: float, nas: float,
    bws: float, is_ip: bool, pot_size: float,
    preflop_pot_type: str, hand_eval: HandEvaluation
) -> Dict[str, Any]:
    """
    Hero acts first (no villain bet to face).
    Determines: CHECK or BET (SMALL/MEDIUM/LARGE) + dollar amount.
    """
    # Bluff activation: flush draw, OESD, or combo draw
    total_outs = 0
    if hand_eval.has_flush_draw:
        total_outs += hand_eval.flush_draw_outs
    if hand_eval.has_oesd:
        total_outs += hand_eval.straight_draw_outs
    elif hand_eval.has_gutshot:
        total_outs += hand_eval.straight_draw_outs
    has_bluff = total_outs >= 6

    check_score = compute_check_score(effective_hps, bws, is_ip)

    best_action    = "Check"
    best_score     = check_score
    best_fraction  = 0.0
    best_label     = "CHECK"

    action_scores: Dict[str, float] = {"check": check_score}

    for label, fraction in BET_SIZES:
        fold_prob, fold_bonus = compute_efe(pot_size, fraction, bws, ras, preflop_pot_type)
        score = compute_action_score(
            effective_hps, ras, nas, bws, fold_bonus, is_ip, has_bluff, fraction
        )
        action_scores[label.lower()] = score

        if score > best_score:
            best_score    = score
            best_action   = label
            best_fraction = fraction
            best_label    = label

    # C-bet frequency pre-filter
    pos_key    = ("IP" if is_ip else "OOP", preflop_pot_type)
    cbet_freq  = CBET_FREQ.get(pos_key, 0.55)
    # Threshold: how much better must BET be than CHECK to actually bet?
    threshold  = check_score + (1.0 - cbet_freq) * 2.0

    if best_label != "CHECK" and best_score < threshold:
        # C-bet frequency says check more often — revert to check
        best_label    = "CHECK"
        best_action   = "Check"
        best_fraction = 0.0

    # Format action text
    if best_label == "CHECK":
        action_text = "Check"
        reasoning_prefix = _build_check_reasoning(effective_hps, bws, hand_eval)
    else:
        bet_dollars = pot_size * best_fraction
        pct         = int(best_fraction * 100)
        action_text = f"Bet {pct}% pot (${bet_dollars:.2f})"
        reasoning_prefix = _build_bet_reasoning(
            best_fraction, effective_hps, bws, ras, nas,
            hand_eval, is_ip, preflop_pot_type
        )

    # Compute final fold probability for response
    final_fold_prob, _ = compute_efe(pot_size, best_fraction, bws, ras, preflop_pot_type)

    return {
        "action": action_text,
        "reasoning": reasoning_prefix,
        "fold_probability": f"{final_fold_prob * 100:.0f}%",
        "action_scores": {k: round(v, 2) for k, v in action_scores.items()},
        "bet_fraction": best_fraction,
    }


# ─────────────────────────────────────────────
#  DEFENSIVE PIPELINE
# ─────────────────────────────────────────────

def make_defensive_decision(
    effective_hps: float, pot_size: float, call_amount: float,
    hand_eval: HandEvaluation, bws: float
) -> Dict[str, Any]:
    """
    Hero faces a villain bet.
    Determines: CALL or FOLD using MDF logic.
    """
    mdf = compute_mdf(pot_size, call_amount)
    pot_odds_pct = (call_amount / (pot_size + call_amount)) * 100

    # Normalise effective_hps to 0-1 scale (max possible HPS ~13)
    hand_rank_normalised = effective_hps / 13.0

    # Always call with monsters
    if effective_hps >= 7.0:
        action = "Call"
        reasoning = (
            f"Monster/strong hand (HPS {effective_hps:.1f}) — always continue vs villain bet. "
            f"Pot odds {pot_odds_pct:.1f}% are easily covered."
        )
        fold_prob, _ = compute_efe(pot_size, call_amount / max(pot_size, 0.01), bws, 0.0, "open_raise")
        return {
            "action": action,
            "reasoning": reasoning,
            "fold_probability": f"{fold_prob * 100:.0f}%",
            "mdf": f"{mdf * 100:.0f}%",
            "pot_odds": f"{pot_odds_pct:.1f}%",
        }

    # Always fold with air
    if effective_hps <= 1.5:
        return {
            "action": "Fold",
            "reasoning": (
                f"No made hand or draw (HPS {effective_hps:.1f}). "
                f"Not worth calling {pot_odds_pct:.1f}% pot odds with air."
            ),
            "fold_probability": "100%",
            "mdf": f"{mdf * 100:.0f}%",
            "pot_odds": f"{pot_odds_pct:.1f}%",
        }

    # MDF decision: defend top MDF% of range
    if hand_rank_normalised >= (1.0 - mdf):
        action = "Call"
        reasoning = (
            f"Hand ranks in top {mdf * 100:.0f}% of range — within MDF threshold. "
            f"Need to defend to avoid being over-bluffed. "
            f"Pot odds: {pot_odds_pct:.1f}% | MDF: {mdf * 100:.0f}%."
        )
    else:
        action = "Fold"
        reasoning = (
            f"Hand ranks below MDF threshold ({mdf * 100:.0f}% defense needed). "
            f"HPS {effective_hps:.1f} is too weak to continue at {pot_odds_pct:.1f}% pot odds."
        )

    fold_prob, _ = compute_efe(pot_size, call_amount / max(pot_size, 0.01), bws, 0.0, "open_raise")
    return {
        "action": action,
        "reasoning": reasoning,
        "fold_probability": f"{fold_prob * 100:.0f}%",
        "mdf": f"{mdf * 100:.0f}%",
        "pot_odds": f"{pot_odds_pct:.1f}%",
    }


# ─────────────────────────────────────────────
#  REASONING TEXT BUILDERS
# ─────────────────────────────────────────────

def _build_check_reasoning(effective_hps: float, bws: float,
                            hand_eval: HandEvaluation) -> str:
    parts = []
    if effective_hps >= 8.0:
        parts.append("Strong hand — check to induce bluffs or allow villain to catch up.")
    elif effective_hps >= 5.0:
        parts.append("Medium-strength hand — check to control pot size and protect equity.")
    else:
        parts.append("Weak holding — check to see a free card.")

    if bws >= 4.0:
        parts.append("Wet board makes large bets risky; checking is safer.")

    if hand_eval.has_flush_draw or hand_eval.has_oesd:
        parts.append("Strong draw — checking also serves as a deceptive slowplay.")

    return " ".join(parts)


def _build_bet_reasoning(fraction: float, effective_hps: float, bws: float,
                          ras: float, nas: float, hand_eval: HandEvaluation,
                          is_ip: bool, preflop_pot_type: str) -> str:
    parts = []

    pct = int(fraction * 100)

    if effective_hps >= 7.5:
        parts.append(f"Powerful hand — betting {pct}% pot for value.")
    elif effective_hps >= 5.0:
        parts.append(f"Solid holding — betting {pct}% pot for value and protection.")
    elif hand_eval.has_flush_draw or hand_eval.has_oesd:
        total_outs = (hand_eval.flush_draw_outs if hand_eval.has_flush_draw else 0) + hand_eval.straight_draw_outs
        parts.append(f"Semi-bluff with {total_outs} outs — betting {pct}% pot builds pot and applies pressure.")
    else:
        parts.append(f"Probing bet {pct}% pot to test villain's range.")

    if ras >= 0.3:
        parts.append("Range favours hero on this board.")
    elif ras <= -0.3:
        parts.append("Villain has range advantage — bet sizing kept conservative.")

    if nas >= 0.5:
        parts.append("Nut advantage is with hero — can bet larger with confidence.")
    elif nas <= -0.5:
        parts.append("Villain holds more nut hands — proceed with caution.")

    pos_str = "IP" if is_ip else "OOP"
    parts.append(f"Hero is {pos_str} in a {preflop_pot_type.replace('_', ' ')}.")

    return " ".join(parts)


def _describe_board(board_cards: List[str], bws: float) -> str:
    """Generate a human-readable board description."""
    if bws <= 2.0:
        texture = "Dry"
    elif bws <= 4.0:
        texture = "Semi-wet"
    else:
        texture = "Wet"

    try:
        cards = [Card(c) for c in board_cards]
        suits = [c.suit for c in cards]
        suit_counts = Counter(suits)
        ranks = sorted([c.rank for c in cards], reverse=True)
        rank_names = [c.rank_name for c in cards]

        suit_desc = ""
        if max(suit_counts.values()) == 3:
            suit_desc = "monotone (flush possible)"
        elif max(suit_counts.values()) == 2:
            suit_desc = "two-tone"
        else:
            suit_desc = "rainbow"

        conn_desc = ""
        connected = sum(1 for i in range(len(ranks) - 1) if ranks[i] - ranks[i+1] == 1)
        if connected >= 2:
            conn_desc = "highly connected"
        elif connected == 1:
            conn_desc = "connected"
        else:
            conn_desc = "disconnected"

        return f"{texture}: {', '.join(rank_names)} — {suit_desc}, {conn_desc}"
    except Exception:
        return f"{texture} board"


# ─────────────────────────────────────────────
#  MAIN ENGINE
# ─────────────────────────────────────────────

class FlopLogicEngine:
    """
    Rush & Cash Flop GTO Decision Engine.
    Gemini extracts cards visually; this engine makes the decision.
    """

    def analyze(
        self,
        hero_cards: List[str],
        board_cards: List[str],
        pot_size: float,
        villain_raise: float,
        hero_position: str,         # "IP" or "OOP"
        villain_position: str,      # "UTG", "MP", "CO", "BTN", "SB", "BB"
        preflop_pot_type: str       # "open_raise", "3bet", "4bet"
    ) -> Dict[str, Any]:
        """
        Full flop analysis.

        Returns a result dict compatible with deep_flop_analyzer response format.
        """
        try:
            is_ip = (hero_position == "IP")
            logger.info(
                f"🎴 FlopLogicEngine: {hero_cards} | Board: {board_cards} "
                f"| Pot: ${pot_size:.2f} | Raise: ${villain_raise:.2f} "
                f"| {hero_position} vs {villain_position} | {preflop_pot_type}"
            )

            # ── Step 1: Evaluate the hand ─────────────
            hand_eval = evaluate_hand(hero_cards, board_cards)

            # ── Step 2: Compute all metrics ───────────
            hps, pair_subtype = compute_hps(hero_cards, board_cards, hand_eval)
            bws               = compute_bws(board_cards)
            ras, ras_label    = compute_ras(hero_position if is_ip else villain_position,
                                            villain_position if is_ip else hero_position,
                                            board_cards)
            nas, nas_label    = compute_nas(hero_position if is_ip else villain_position,
                                            villain_position if is_ip else hero_position,
                                            board_cards)
            erf               = compute_erf(hand_eval, is_ip, bws, pair_subtype)
            effective_hps     = hps * erf

            logger.info(
                f"Metrics → HPS={hps:.2f}, BWS={bws:.2f}, RAS={ras:.3f}({ras_label}), "
                f"NAS={nas:.3f}({nas_label}), ERF={erf:.3f}, EffHPS={effective_hps:.2f}"
            )

            # ── Step 3: Offensive or Defensive? ───────
            if villain_raise > 0:
                # Hero faces a bet — defensive pipeline
                decision = make_defensive_decision(
                    effective_hps, pot_size, villain_raise, hand_eval, bws
                )
            else:
                # Hero acts first — offensive pipeline
                decision = make_offensive_decision(
                    effective_hps, ras, nas, bws, is_ip,
                    pot_size, preflop_pot_type, hand_eval
                )

            # ── Step 4: Build descriptions ────────────
            board_desc = _describe_board(board_cards, bws)
            hand_desc  = hand_eval.description
            if hand_eval.draw_description and "No " not in hand_eval.draw_description:
                hand_desc += f" + {hand_eval.draw_description}"

            # ── Step 5: EFE for display ───────────────
            display_fold_prob = decision.get("fold_probability", "N/A")
            best_fraction     = decision.get("bet_fraction", 0.0)
            _, efe_dollars    = compute_efe(pot_size, best_fraction, bws, ras, preflop_pot_type)

            metrics = {
                "hps":          round(hps, 2),
                "effective_hps": round(effective_hps, 2),
                "bws":          round(bws, 2),
                "ras":          ras_label,
                "ras_numeric":  round(ras, 3),
                "nas":          nas_label,
                "nas_numeric":  round(nas, 3),
                "erf":          round(erf, 3),
                "pair_subtype": pair_subtype,
                "fold_probability": display_fold_prob,
                "efe_dollars":  f"${efe_dollars:.2f}",
                "action_scores": decision.get("action_scores", {}),
            }

            return {
                "success":        True,
                "action":         decision["action"],
                "reasoning":      decision["reasoning"],
                "board_description": board_desc,
                "hand_description":  hand_desc,
                "metrics":        metrics,
            }

        except Exception as e:
            logger.error(f"❌ FlopLogicEngine error: {e}", exc_info=True)
            return {
                "success": False,
                "error":   str(e)
            }
