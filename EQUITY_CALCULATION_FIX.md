# Equity Calculation Fix Summary

**Date:** January 7, 2026  
**Issue:** Turn equity showing 30% instead of correct 8.7% for gutshot draws  
**Status:** ✅ FIXED

---

## 🐛 The Bug

### User's Reported Issue:
- **Hand:** 6♦5♦
- **Board (Turn):** 8♣ A♥ 3♠ 9♦
- **Actual Situation:** 4-out gutshot straight draw (need a 7)
- **Expected Equity:** 4/46 = **8.7%**
- **Displayed Equity:** **30.0%** ❌ (WRONG!)

### Root Cause:
The `_calculate_equity()` method in `turn_river_analyzer.py` was using `max(draw_equity, made_equity)` which incorrectly selected the higher of:
- Draw equity: 8.7% (correct for 4 outs)
- Showdown equity: 30% (hardcoded for "weak" hands)

**Result:** The program showed 30% instead of 8.7%

---

## ✅ The Fix

### Changed Logic:
```python
# OLD (BUGGY):
return max(draw_equity, made_equity)

# NEW (CORRECT):
if outs > 0:
    return draw_equity  # Use ONLY draw equity when we have outs
else:
    return made_equity  # Use showdown equity only when no outs
```

### Why This Is Correct:
1. **When you have outs:** Your equity comes from hitting those outs, not your current hand
2. **When you have no outs:** Your equity comes from showdown value of your current hand
3. **You can't "add" or "max" these together** - they represent different scenarios

---

## 📊 Test Results

### Your Specific Hand (6♦5♦):
```
✓ OLD method: 30.0% (WRONG - used max(8.7%, 30%))
✓ NEW method: 8.7% (CORRECT - used draw equity only)
✓ Expected:   8.7%
```

### Additional Test Cases:
```
✓ Flush draw (9 outs): 19.6% (expected 19.6%)
✓ OESD (8 outs): 17.4% (expected 17.4%)
✓ Pocket pair (0 outs, strong): 70.0% (expected 70.0%)
✓ Top pair (0 outs, medium): 50.0% (expected 50.0%)
```

**All tests passed! ✅**

---

## 📁 Files Modified

1. **backend/turn_river_analyzer.py**
   - Modified `_calculate_equity()` method (lines 231-261)
   - Changed from `max()` logic to if/else prioritization
   - Added detailed comments explaining the fix

2. **backend/test_equity_simple.py** (NEW)
   - Created comprehensive test suite
   - Tests all draw scenarios and made hands
   - Verifies the fix works correctly

---

## 🎯 Impact

### Before Fix:
- ❌ Gutshot draws showed 30% equity (too high)
- ❌ Any weak draw showed inflated equity
- ❌ Decision-making was incorrect (calling when should fold)

### After Fix:
- ✅ Gutshot draws show correct 8.7% equity
- ✅ All draws show accurate equity based on outs
- ✅ Decision-making is now mathematically correct
- ✅ Made hands without draws still use showdown equity correctly

---

## 💡 Key Insights

### The Fundamental Issue:
The program was treating **draw equity** and **showdown equity** as interchangeable, when they actually represent:

- **Draw Equity:** "What % chance do I have of hitting my draw?"
  - Example: 4 outs / 46 cards = 8.7%

- **Showdown Equity:** "If no more cards come, what % chance do I win?"
  - Example: 6-high has ~0% showdown value

**These can't be combined with max() - when you have outs, use draw equity!**

---

## 🧪 How to Test

Run the test file:
```bash
python backend/test_equity_simple.py
```

Expected output:
```
OK ALL TESTS PASSED! Equity calculation is now correct.
```

---

## 📚 Technical Details

### Equity Formula (Turn):

**With Outs (Drawing Hand):**
```
equity = (outs / 46) × 100
```

**Without Outs (Made Hand):**
```
equity = estimated_showdown_value
  - Monster: 85%
  - Strong: 70%
  - Medium: 50%
  - Weak: 20%
  - Air: 10%
```

**Important:** Never use `max(draw_equity, showdown_equity)` - pick one based on whether you have outs!

---

## ✅ Verification Checklist

- [x] Bug identified (max() logic issue)
- [x] Fix implemented in turn_river_analyzer.py
- [x] Test suite created
- [x] All tests passing
- [x] User's specific case (6♦5♦) now shows 8.7%
- [x] Other scenarios still work correctly
- [x] Documentation created

---

**Status:** ✅ COMPLETE - Equity calculation is now mathematically correct!
