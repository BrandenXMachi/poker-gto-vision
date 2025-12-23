"""
Test Hand Evaluator with the exact scenario from the user's issue
Hero: 7♦7♣ on Board: K♠9♣A♠
"""

from hand_evaluator import evaluate_hand

def test_user_scenario():
    """Test the exact scenario: 7 of Diamonds, 7 of Clubs on K♠9♣A♠"""
    
    print("=" * 70)
    print("🧪 Testing User's Exact Scenario")
    print("=" * 70)
    
    hero_cards = ["7 of Diamonds", "7 of Clubs"]
    flop_cards = ["King of Spades", "9 of Clubs", "Ace of Spades"]
    
    print(f"\n🎴 HERO CARDS: {hero_cards}")
    print(f"🎴 FLOP CARDS: {flop_cards}")
    print()
    
    evaluation = evaluate_hand(hero_cards, flop_cards)
    
    print("📊 EVALUATION RESULTS:")
    print("-" * 70)
    print(f"Made Hand: {evaluation.made_hand}")
    print(f"Hand Strength: {evaluation.strength}")
    print(f"Description: {evaluation.description}")
    print()
    
    print("🎯 DRAW ANALYSIS:")
    print("-" * 70)
    print(f"Flush Draw: {evaluation.has_flush_draw}")
    print(f"Flush Draw Outs: {evaluation.flush_draw_outs}")
    print(f"Backdoor Flush Draw: {evaluation.has_backdoor_flush_draw}")
    print(f"OESD: {evaluation.has_oesd}")
    print(f"Gutshot: {evaluation.has_gutshot}")
    print(f"Straight Draw Outs: {evaluation.straight_draw_outs}")
    print(f"Draw Description: {evaluation.draw_description}")
    print()
    
    print("✅ EXPECTED RESULTS:")
    print("-" * 70)
    print("❌ NO Flush Draw (hero has 1 diamond + 1 club, board has 2 spades + 1 club)")
    print("❌ NO Backdoor Flush Draw")
    print("❌ NO Straight Draw (7-7 can't connect with K-9-A)")
    print("✅ Made Hand: Pocket pair (low pair)")
    print("✅ Strength: WEAK (low pair on high card board)")
    print()
    
    print("🎯 VALIDATION:")
    print("-" * 70)
    
    # Validate results
    issues = []
    
    if evaluation.has_flush_draw:
        issues.append("❌ FALSE POSITIVE: Has flush draw (should be False)")
    else:
        print("✅ Correctly identified NO flush draw")
    
    if evaluation.has_backdoor_flush_draw:
        issues.append("❌ FALSE POSITIVE: Has backdoor flush draw (should be False)")
    else:
        print("✅ Correctly identified NO backdoor flush draw")
    
    if evaluation.has_oesd or evaluation.has_gutshot:
        issues.append("❌ FALSE POSITIVE: Has straight draw (should be False)")
    else:
        print("✅ Correctly identified NO straight draw")
    
    if evaluation.made_hand != "pair":
        issues.append(f"❌ Wrong made hand: {evaluation.made_hand} (should be 'pair')")
    else:
        print("✅ Correctly identified pocket pair")
    
    if evaluation.strength not in ["weak", "medium"]:
        issues.append(f"❌ Wrong strength: {evaluation.strength} (should be 'weak' or 'medium')")
    else:
        print(f"✅ Correctly classified as {evaluation.strength}")
    
    print()
    
    if issues:
        print("🚨 ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("🎉 ALL TESTS PASSED! The fix is working correctly!")
    
    print("=" * 70)
    print()
    
    return len(issues) == 0


def test_additional_scenarios():
    """Test a few more scenarios to ensure robustness"""
    
    print("=" * 70)
    print("🧪 Testing Additional Scenarios")
    print("=" * 70)
    print()
    
    # Scenario 1: Real flush draw
    print("📍 Scenario 1: Real Flush Draw")
    print("-" * 70)
    hero1 = ["Ace of Hearts", "King of Hearts"]
    flop1 = ["Queen of Hearts", "9 of Hearts", "2 of Spades"]
    eval1 = evaluate_hand(hero1, flop1)
    print(f"Hero: {hero1}")
    print(f"Flop: {flop1}")
    print(f"Has Flush Draw: {eval1.has_flush_draw} (Expected: True)")
    print(f"Outs: {eval1.flush_draw_outs} (Expected: 9)")
    print(f"✅ PASS" if eval1.has_flush_draw else "❌ FAIL")
    print()
    
    # Scenario 2: No flush draw (hero has no matching suits)
    print("📍 Scenario 2: No Flush Draw")
    print("-" * 70)
    hero2 = ["Ace of Hearts", "King of Clubs"]
    flop2 = ["Queen of Spades", "9 of Spades", "2 of Diamonds"]
    eval2 = evaluate_hand(hero2, flop2)
    print(f"Hero: {hero2}")
    print(f"Flop: {flop2}")
    print(f"Has Flush Draw: {eval2.has_flush_draw} (Expected: False)")
    print(f"✅ PASS" if not eval2.has_flush_draw else "❌ FAIL")
    print()
    
    # Scenario 3: OESD
    print("📍 Scenario 3: Open-Ended Straight Draw")
    print("-" * 70)
    hero3 = ["Jack of Hearts", "10 of Clubs"]
    flop3 = ["9 of Spades", "8 of Diamonds", "2 of Hearts"]
    eval3 = evaluate_hand(hero3, flop3)
    print(f"Hero: {hero3}")
    print(f"Flop: {flop3}")
    print(f"Has OESD: {eval3.has_oesd} (Expected: True)")
    print(f"Outs: {eval3.straight_draw_outs} (Expected: 8)")
    print(f"✅ PASS" if eval3.has_oesd else "❌ FAIL")
    print()
    
    print("=" * 70)
    print()


if __name__ == "__main__":
    print("\n")
    print("🎯 HAND EVALUATOR TEST SUITE")
    print("Testing the fix for flush draw false positives\n")
    
    # Test user's exact scenario
    user_test_passed = test_user_scenario()
    
    # Test additional scenarios
    test_additional_scenarios()
    
    if user_test_passed:
        print("\n✅ PRIMARY TEST PASSED - Fix is working correctly!")
    else:
        print("\n❌ PRIMARY TEST FAILED - Issue still exists!")
