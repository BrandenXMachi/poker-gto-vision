# Flop Analysis Fix: Medium Hands Max Call Limits

## 🐛 Bug Description

The flop analyzer was recommending to **FOLD** with **QJ on Q♥ 8♣ 6♠** (top pair + backdoor draws) in position vs early open - a clear error.

### Example from Screenshot:
- **Hand:** Queen of Spades, Jack of Spades  
- **Board:** 8♣ Q♥ 6♠
- **Situation:** In Position vs UTG open
- **Recommendation:** ❌ **FOLD** (Incorrect!)
- **Should be:** ✅ **CALL up to 50% pot** (Correct!)

---

## 🔍 Root Cause Analysis

### Hand Evaluator Classification:

Looking at `hand_evaluator.py`, pairs are classified as:
```python
if eval.made_hand_rank >= 113:  # Pair of Kings or better
    eval.strength = "strong"
elif eval.made_hand_rank >= 110:  # Pair of Tens or better  
    eval.strength = "medium"
else:
    eval.strength = "weak"  # Low pair
```

**Your QJ hand:**
- Pair of Queens = rank 112 (100 + 12)
- 112 >= 110? YES → **"medium"** ✅ (Correctly classified!)

### Flop Analyzer Bug:

The `_villain_opened_hero_called()` method had:
```python
elif hand_str == "medium":
    if early_position:
        return {"action": "Fold", "reasoning": "Medium vs early open IP - fold"}  # ❌ TOO TIGHT!
```

**The bug:** ALL medium hands were being folded in position vs early opens, even with reasonable equity!

---

## ✅ The Fix: Max Call Limits

Instead of folding, medium hands now have **maximum call amounts** based on:
1. **Position** (IP vs OOP)
2. **Villain range** (early vs late position)
3. **Board texture** (dry vs wet)
4. **Preflop action** (open, 3-bet, 4-bet)

---

## 💰 Complete Max Call Limits Reference

### **Scenario 1: Villain Opened, Hero Called (Most Common)**

#### In Position (IP):

| Villain Position | Board | Max Call | Example |
|-----------------|-------|----------|---------|
| Early (UTG/MP) | Dry | **50% pot** | QJ on Q♥ 8♣ 6♠ - Call up to 50% |
| Early (UTG/MP) | Wet | **40% pot** | T9 on T♥ 8♥ 6♠ - Call up to 40% |
| Late (CO/BTN) | Dry | **75% pot** | QJ on Q♥ 8♣ 6♠ - Call up to 75% |
| Late (CO/BTN) | Wet | **60% pot** | T9 on T♥ 8♥ 6♠ - Call up to 60% |

#### Out of Position (OOP):

| Villain Position | Board | Max Call | Reasoning |
|-----------------|-------|----------|-----------|
| Early (UTG/MP) | Any | **33% pot** | No position + tight range |
| Late (CO/BTN) | Any | **50% pot** | Wider range = can call more |

---

### **Scenario 2: Hero 3-Bet, Villain Called**

#### In Position (IP):
- **Action:** Check back for pot control
- **If villain bets:** Call up to **50% pot**

#### Out of Position (OOP):
- **Max call:** **40% pot**
- Villain has strong flatting range

---

### **Scenario 3: Villain 3-Bet, Hero Called**

#### In Position (IP):

| Villain Position | Max Call | Reasoning |
|-----------------|----------|-----------|
| Early (UTG/MP) | **40% pot** | Very tight 3-bet range |
| Late (CO/BTN) | **50% pot** | Wider 3-bet range |

#### Out of Position (OOP):
- **Max call:** **33% pot**
- Fold to anything larger

---

### **Scenario 4: Villain 4-Bet, Hero Called (Rare)**

#### Any Position:
- **Max call:** **40% pot MAX**
- Villain has KK+/AK most of the time
- Medium hands barely have equity

---

## 📊 Hand Strength Classifications

### What is "Medium" Strength?

**Made Hands:**
- **Pairs:** TT, JJ, QQ (ranks 110-112)
  - Top pair weak kicker (Q8, J7)
  - Overpair on higher boards
  - Second pair good kicker

**Draws:**
- Flush draws (9 outs)
- Open-ended straight draws (8 outs)
- Combo draws if not nut draws

### What is "Strong" Strength?

**Made Hands:**
- **Pairs:** KK+ (rank 113+)
  - Top pair strong kicker (AK, KQ)
  - Overpairs on low boards
- **Two pair**
- **Trips**

**Draws:**
- Combo draws (flush + straight)
- Nut draws with pair

### What is "Monster" Strength?

- Straights
- Flushes
- Full houses
- Quads

---

## 🎯 Strategic Rationale

### Why Max Call Limits Instead of Folding?

**Problem with "Fold":**
- Too exploitable - opponent can bet anything and win
- Wastes equity on medium hands
- Doesn't account for position advantage

**Solution with "Call limit X% pot":**
- **Disciplined** - Won't call massive bets with marginal hands
- **Flexible** - Can call small bets profitably
- **Position-aware** - Calls more IP, less OOP
- **Opponent-adjusted** - Calls less vs tight ranges

### Example: QJ on Q♥ 8♣ 6♠ vs UTG Open (IP)

**Before Fix:**
- Classification: Medium
- Action: ❌ **FOLD**
- Problem: Folding top pair is terrible!

**After Fix:**
- Classification: Medium ✅
- Max call: **50% pot**
- Action: ✓ Call if villain bets ≤50% pot, fold if >50%
- Reasoning: You have position, reasonable equity, but not strong enough for huge bets

---

## 📁 Files Modified

### `flop_gto_analyzer.py`

**Methods Updated:**
1. `_villain_opened_hero_called()` - Added max call limits for IP/OOP
2. `_villain_called_hero_3bet()` - Added 40-50% pot limits
3. `_villain_3bet_hero_called()` - Added 33-50% pot limits by position

**Total Changes:** ~30 lines modified across 3 methods

---

## ✅ Testing Your Fix

### Test Case 1: QJ on Q♥ 8♣ 6♠
- **Situation:** IP vs UTG open, dry board
- **Expected:** "Call limit 50% pot"
- **Status:** ✅ Fixed

### Test Case 2: T9 on T♥ 8♥ 6♠
- **Situation:** IP vs UTG open, wet board
- **Expected:** "Call limit 40% pot"
- **Status:** ✅ Fixed

### Test Case 3: 88 on A♠ K♠ 2♣
- **Situation:** OOP vs CO open, wet board
- **Expected:** "Check-call limit 50% pot"
- **Status:** ✅ Fixed

---

## 💡 Key Takeaways

1. **Medium hands should NEVER auto-fold** in position
2. **Max call limits** prevent calling too much with marginal hands
3. **Position matters** - Call more IP, less OOP
4. **Opponent range matters** - Call less vs tight ranges
5. **Board texture matters** - Call less on wet boards vs early positions

---

**Date:** January 1, 2026  
**Status:** ✅ Complete and Tested  
**Impact:** Fixed major leak where top pair/medium hands were folding incorrectly
