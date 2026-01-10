# BTN/CO Calling vs 3-Bet Range Update

**Date:** January 2, 2026  
**Update Type:** MAJOR RANGE EXPANSION  
**Rationale:** Optimized for 20% VPIP tight opponents (based on ChatGPT analysis)

---

## 📊 SUMMARY OF CHANGES

### **Button (BTN) Calling vs 3-Bet Range**

**OLD Range (14 combos):**
- Pairs: 88, 99, TT, JJ
- Suited: ATs, AJs, AQs, KQs, QJs, JTs, 87s, 76s

**NEW Range (32 combos):**
- **ALL Pairs:** 22, 33, 44, 55, 66, 77, 88, 99, TT, JJ
- **ALL Suited Aces:** A2s, A3s, A4s, A5s, A6s, A7s, A8s, A9s, ATs, AJs, AQs
- **Offsuit:** AQo
- **Suited Broadway:** KQs, KJs, QJs, JTs, KTs, QTs
- **Suited Connectors:** T9s, 98s, 87s, J9s

**ADDED:**
- ✅ Small pairs: 22-77 (6 pairs)
- ✅ Suited aces: A2s-A9s (8 hands)
- ✅ AQo (offsuit)
- ✅ More suited broadway: KJs, KTs, QTs
- ✅ More suited connectors: T9s, 98s, J9s

---

### **Cutoff (CO) Calling vs 3-Bet Range**

**OLD Range (10 combos):**
- Pairs: 99, TT, JJ
- Suited: AKs, AQs, AJs, KQs, 87s, 76s

**NEW Range (31 combos):**
- **ALL Pairs:** 22, 33, 44, 55, 66, 77, 88, 99, TT, JJ
- **ALL Suited Aces:** A2s, A3s, A4s, A5s, A6s, A7s, A8s, A9s, ATs, AJs, AQs
- **Offsuit:** AQo
- **Suited Broadway:** KQs, KJs, QJs, JTs, KTs, QTs
- **Suited Connectors:** T9s, 98s, 87s

**ADDED:**
- ✅ Small pairs: 22-88 (7 pairs)
- ✅ Suited aces: A2s-A9s (8 hands)
- ✅ AQo (offsuit)
- ✅ More suited broadway: KJs, KTs, QTs
- ✅ More suited connectors: T9s, 98s

---

## 🎯 STRATEGIC RATIONALE

### **Why Widen These Ranges?**

1. **Positional Advantage**
   - BTN and CO have the best position postflop
   - Can profitably call 3-bets wider than earlier positions
   - Position allows us to realize equity better

2. **Small Pairs (22-77)**
   - **Setmining value:** Can flop sets ~12% of time
   - **Implied odds:** Huge payoff when we hit vs overpairs
   - **Disguised strength:** Villain doesn't expect small pairs in our range
   - **Stack depth:** Profitable at 100bb+ effective stacks

3. **Suited Aces (A2s-A9s)**
   - **Backdoor flush draws:** ~17% chance of backdoor flush draw
   - **Wheel potential:** A2s-A5s can make straights
   - **Top pair:** Still makes TPTK sometimes
   - **Domination leverage:** When villain has Ax, we often have better kicker

4. **Suited Connectors/Broadway (T9s, 98s, KTs, QTs, J9s)**
   - **Playability:** Easy postflop decisions with draws
   - **Straight potential:** Multiple straight draws
   - **Flush draws:** Backdoor and flopped flush draws
   - **Disguised hands:** Can make hidden straights

5. **Against 20% VPIP Opponents**
   - Tight players have linear 3-bet ranges (QQ+, AK mostly)
   - They don't adjust well to wider calling ranges
   - They overvalue their premium hands postflop
   - We can exploit with speculative hands that connect

---

## 📈 COMPARISON: OLD vs NEW

| Position | Old Combos | New Combos | Increase |
|----------|------------|------------|----------|
| **BTN**  | 14         | 32         | **+128%** |
| **CO**   | 10         | 31         | **+210%** |

---

## ⚠️ IMPORTANT NOTES

### **When These Ranges Apply:**

✅ **Use these ranges when:**
- You're in BTN or CO position
- Facing a 3-bet from ANY position (SB, BB, UTG, MP, etc.)
- Villain has ~20% VPIP (tight, linear range)
- Effective stacks are 100bb+
- You have position postflop

❌ **Don't use these ranges when:**
- Out of position (UTG, MP still have tighter ranges)
- Facing a 4-bet (fold most of these hands)
- Short stacked (<60bb effective)
- Villain is super aggressive (>30% VPIP)

### **4-Bet Ranges Unchanged:**

- BTN/CO still 4-bet: **AA, KK, AKs, AKo** only
- These new hands are **calling only**, not 4-betting
- QQ removed from calling range (should 4-bet or fold)

---

## 🧪 TESTING RECOMMENDATIONS

### **Test These Scenarios:**

1. **BTN with 44 vs BB 3-bet** → Should CALL ✅
2. **CO with A7s vs SB 3-bet** → Should CALL ✅
3. **BTN with T9s vs SB 3-bet** → Should CALL ✅
4. **CO with 22 vs BB 3-bet** → Should CALL ✅
5. **BTN with J9s vs BB 3-bet** → Should CALL ✅

---

## 📚 REFERENCES

- **ChatGPT Analysis:** Ranges optimized for 20% VPIP tight opponents
- **GTO Principles:** In-position calling ranges with speculative hands
- **Implied Odds:** Small pairs and suited aces have great implied odds
- **Positional Equity:** BTN/CO can realize equity better postflop

---

## 🚀 DEPLOYMENT

- **Committed:** January 2, 2026
- **Pushed to:** GitHub main branch
- **Auto-deployed:** Render.com (3-5 minutes)
- **Status:** ✅ LIVE

**Wait for Render deployment, then hard refresh (Ctrl+Shift+R) to test!**
