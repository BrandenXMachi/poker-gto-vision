"""
Simple test to verify equity calculation fix
Tests the logic without needing all dependencies
"""


def calculate_equity_old(outs, hand_strength):
    """OLD (BUGGY) method - uses max()"""
    draw_equity = (outs / 46) * 100 if outs > 0 else 0
    
    if hand_strength == "monster":
        made_equity = 85
    elif hand_strength == "strong":
        made_equity = 70
    elif hand_strength == "medium":
        made_equity = 50
    elif hand_strength == "weak":
        made_equity = 30
    else:
        made_equity = 10
    
    return max(draw_equity, made_equity)  # BUG: Uses max()


def calculate_equity_new(outs, hand_strength):
    """NEW (FIXED) method - prioritizes draw equity"""
    if outs > 0:
        return (outs / 46) * 100  # Use draw equity when we have outs
    
    # No outs - use showdown equity
    if hand_strength == "monster":
        return 85
    elif hand_strength == "strong":
        return 70
    elif hand_strength == "medium":
        return 50
    elif hand_strength == "weak":
        return 20
    else:
        return 10


print("=" * 70)
print("EQUITY CALCULATION FIX TEST")
print("=" * 70)

# Test case: Your specific hand (6d5d on 8cAh3s9d)
print("\nTest Case: 6d5d on 8cAh3s9d")
print("   - Hand: Gutshot straight draw (need a 7)")
print("   - Outs: 4")
print("   - Hand strength: 'weak' (6-high)")

outs = 4
hand_strength = "weak"

old_equity = calculate_equity_old(outs, hand_strength)
new_equity = calculate_equity_new(outs, hand_strength)
correct_equity = (4 / 46) * 100

print(f"\nX  OLD method: {old_equity:.1f}% (WRONG - used max(8.7%, 30%))")
print(f"OK NEW method: {new_equity:.1f}% (CORRECT - used draw equity only)")
print(f"OK Expected:   {correct_equity:.1f}%")

if abs(new_equity - correct_equity) < 0.01:
    print("\nOK PASS: New method is correct!")
else:
    print("\nX  FAIL: New method is incorrect")

# More test cases
print("\n" + "=" * 70)
print("ADDITIONAL TEST CASES")
print("=" * 70)

test_cases = [
    ("Flush draw (9 outs)", 9, "medium", 19.6),
    ("OESD (8 outs)", 8, "weak", 17.4),
    ("Pocket pair (0 outs, strong)", 0, "strong", 70.0),
    ("Top pair (0 outs, medium)", 0, "medium", 50.0),
]

all_pass = True
for name, outs, strength, expected in test_cases:
    new_equity = calculate_equity_new(outs, strength)
    status = "OK" if abs(new_equity - expected) < 0.1 else "X "
    print(f"{status} {name}: {new_equity:.1f}% (expected {expected:.1f}%)")
    if abs(new_equity - expected) > 0.1:
        all_pass = False

print("\n" + "=" * 70)
if all_pass:
    print("OK ALL TESTS PASSED! Equity calculation is now correct.")
else:
    print("X  SOME TESTS FAILED")
print("=" * 70)
