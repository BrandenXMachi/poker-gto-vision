# Turn/River Mode Documentation

## 🎴 Overview

Turn/River (T/R) Mode is a **mathematical decision-making analyzer** for turn and river situations. Unlike "Odds Mode" which relied on AI guessing, T/R Mode uses:

- ✅ **Gemini for visual extraction** (fast, accurate)
- ✅ **Your existing hand_evaluator.py** (precise hand strength)
- ✅ **Real pot odds calculations** (actual math, not AI estimates)
- ✅ **Structured decision logic** (based on equity, outs, bet sizing)

---

## 🎯 Key Features

### **1. Automatic Street Detection**
- Counts board cards: 4 = Turn, 5 = River
- Different equity calculations for each street
- Turn: Considers outs and draws
- River: Pure showdown equity

### **2. Real Mathematics**
- **Pot Odds:** Actual calculation, not AI guess
- **Outs Counting:** Accurate flush/straight draw detection
- **Equity:** Turn uses outs/46 formula, River uses hand strength
- **EV Calculation:** (Equity × Pot) - Call Amount

### **3. Position-Agnostic Design**
- Assumes heads-up (1 opponent) for simplicity
- No position input needed
- Focuses purely on cards + math
- Can be enhanced later with preflop/flop context

### **4. Bet Sizing Classification**
```
Call Amount / Pot = Ratio

Ratio < 0.33  → Small bet (< 33% pot)
Ratio < 0.67  → Medium bet (33-67% pot)  
Ratio < 1.0   → Large bet (67-100% pot)
Ratio ≥ 1.0   → Overbet (> pot)
```

---

## 📊 Decision Framework

### **TURN DECISIONS:**

#### **Strong Hands (Monster/Strong):**
- **Small/Medium bets:** Always call
- **Large bets/Overbets:** Call (strong showdown value)

#### **Drawing Hands:**
| Outs | Draw Type | Decision Logic |
|------|-----------|----------------|
| 15+ | Combo draw | Call if equity > pot odds |
| 9 | Flush draw | Call if equity > pot odds |
| 8 | OESD | Call if equity > pot odds |
| 4 | Gutshot | Need 10% safety margin |
| 2 | Pair to trips | Need great price |

**Formula:** Equity = (Outs / 46) × 100%

#### **Medium Hands (Top pair weak kicker, etc.):**
- **Small bet** (< 33%): Call
- **Medium bet** (< 40% pot odds): Call
- **Large bet:** Fold

#### **Weak Hands:**
- **< 25% pot odds:** Call as bluff catcher
- **> 25% pot odds:** Fold

---

### **RIVER DECISIONS:**

#### **Strong Hands (Monster/Strong):**
- Always call for value

#### **Medium Hands (Bluff catchers):**
- **Small bet** (< 33%): Call as bluff catcher
- **Medium bet** (< 40%) on **dry board:** Call
- **Medium bet** (< 40%) on **wet board:** Fold (draws got there)
- **Large bet:** Fold

#### **Weak Hands:**
- **< 25% pot odds:** Call as pure bluff catcher
- **> 25% pot odds:** Fold

#### **Air/Nothing:**
- Always fold

---

## 📁 File Structure

```
backend/
├── turn_river_analyzer.py    # New T/R analyzer
├── hand_evaluator.py          # Reused for hand strength
├── main.py                    # Updated with "tr" mode routing
└── gemini_only_analyzer.py    # Old odds mode (kept for compatibility)
```

---

## 🔧 API Usage

### **Endpoint:** `POST /analyze`

### **Parameters:**
```
image: File (required)
blinds: "0.02/0.05" (required)
ai_mode: "tr" (required)
```

### **Example Request:**
```bash
curl -X POST http://localhost:8000/analyze \
  -F "image=@poker_table.png" \
  -F "blinds=0.05/0.10" \
  -F "ai_mode=tr"
```

### **Response Format:**
```json
{
  "success": true,
  "ai_mode": "tr",
  "extracted_data": {
    "hero_cards": ["Ace of Spades", "King of Spades"],
    "board_cards": ["Queen of Hearts", "Jack of Diamonds", "Ten of Clubs", "4 of Hearts"],
    "pot_size": "$10.50",
    "call_amount": "$5.00",
    "street": "TURN",
    "bet_category": "medium"
  },
  "analysis": {
    "hand_strength": {
      "made_hand": "straight",
      "description": "Broadway straight (A-K-Q-J-T)",
      "strength_category": "monster"
    },
    "outs": {
      "count": 0,
      "types": []
    },
    "equity": {
      "value": "85.0%",
      "calculation": "Monster made hand estimated equity vs opponent"
    },
    "pot_odds": {
      "percent": "32.3%",
      "ratio": "3.1:1",
      "calculation": "$5.00 to win $15.50"
    },
    "expected_value": {
      "value": "+$3.93",
      "value_bb": "+39.3 BB",
      "calculation": "(85.0% × $10.50) - $5.00 = +$3.93"
    }
  },
  "recommendation": {
    "action": "Call",
    "reasoning": "Monster hand getting good price. With 85.0% equity vs 32.3% pot odds, this is a clear call."
  }
}
```

---

## 💡 Example Scenarios

### **Example 1: Flush Draw on Turn**

**Situation:**
- Hero: 9♥ 8♥
- Board: K♥ 7♥ 2♣ 4♦ (turn)
- Pot: $10
- Call: $5

**Analysis:**
```
Outs: 9 (flush draw)
Equity: 9/46 = 19.6%
Pot Odds: $5 / $15 = 33.3%
Decision: FOLD (19.6% < 33.3%)
Reasoning: "Draw not getting right price. Need 33.3% equity but only have 19.6% with 9 outs."
```

### **Example 2: Top Pair on River**

**Situation:**
- Hero: A♠ K♦
- Board: K♥ 9♠ 5♣ 3♦ 2♥ (river)
- Pot: $20
- Call: $10

**Analysis:**
```
Hand: Top pair, top kicker
Strength: Strong
Pot Odds: $10 / $30 = 33.3%
Equity: 75% (strong hand)
Decision: CALL
Reasoning: "Strong hand on river with 75.0% estimated equity. Clear call for value."
```

### **Example 3: Missed Draw on River**

**Situation:**
- Hero: 9♥ 8♥ (missed flush)
- Board: K♥ 7♥ 2♣ 4♦ A♠ (river)
- Pot: $15
- Call: $10

**Analysis:**
```
Hand: 9-high (air)
Strength: Air
Pot Odds: $10 / $25 = 40%
Decision: FOLD
Reasoning: "No showdown value on river. Easy fold to any bet."
```

---

## 🆚 Comparison: Old Odds Mode vs New T/R Mode

| Feature | Old "Odds" Mode | New "T/R" Mode |
|---------|-----------------|----------------|
| **Extraction** | Gemini (all-in-one) | Gemini (extraction only) |
| **Hand Strength** | AI guesses | hand_evaluator.py (accurate) |
| **Pot Odds** | AI estimates | Real math |
| **Equity** | AI guesses | Outs formula (turn) / strength-based (river) |
| **Decision Logic** | AI judgment | Structured rules |
| **Street Detection** | Manual/unreliable | Automatic (counts cards) |
| **Outs Counting** | AI estimates | Precise calculation |
| **Position Awareness** | Claims to ignore, but inconsistent | Truly position-agnostic |
| **Reliability** | ❌ Inconsistent | ✅ Consistent |
| **Educational** | ❌ Black box | ✅ Shows calculations |

---

## 🔮 Future Enhancements

### **Phase 1: Context Integration (Future)**
When user goes Preflop → Flop → Turn/River in sequence:
- Import preflop action history
- Import flop decisions
- Better opponent range estimation
- More accurate equity calculations

### **Phase 2: Multiple Opponents (Future)**
- Adjust equity for multiway pots
- Different decision thresholds
- Consider dead money

### **Phase 3: Advanced Features (Future)**
- Pot commitment detection
- Stack-to-pot ratio (SPR) adjustments
- Blocker effects
- Range-based equity (vs specific opponents)

---

## ✅ Testing

### **Test Cases:**

1. **Turn with flush draw**
   - Should calculate outs correctly
   - Should use outs/46 formula
   - Should compare to pot odds

2. **River with top pair**
   - Should classify as "strong"
   - Should call reasonable bets
   - Should fold to overbets

3. **River with missed draw**
   - Should classify as "air"
   - Should fold unless incredible price

4. **Turn checked to hero**
   - Should recommend "Check"
   - No EV calculation needed

---

## 📝 Summary

**Turn/River Mode** replaces the unreliable "Odds Mode" with:
- ✅ Real mathematics instead of AI guessing
- ✅ Structured decision logic
- ✅ Automatic street detection
- ✅ Accurate hand evaluation
- ✅ Educational pot odds display

**Use T/R Mode when:**
- You're on the turn or river
- You want mathematical analysis
- You need accurate equity calculations
- You want to see the math behind decisions

**Date Created:** January 1, 2026  
**Status:** ✅ Complete and Ready for Testing  
**Mode:** `ai_mode=tr`
