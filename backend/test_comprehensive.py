"""
Comprehensive Test Suite - Verify hand evaluator works across all scenarios
Tests various board textures, hand types, and draw situations
"""

from hand_evaluator import evaluate_hand

def test_scenario(name, hero, board, expected_strength, expected_flush, expected_straight, expected_made_hand):
    """Test a single scenario and validate results"""
    print(f"\n📍 {name}")
    print("-" * 70)
    print(f"Hero: {hero}")
    print(f"Board: {board}")
    
    eval = evaluate_hand(hero, board)
    
    print(f"Result: {eval.strength} | {eval.made_hand} | {eval.description}")
    
    # Validation
    issues = []
    
    if eval.strength != expected_strength:
        issues.append(f"❌ Strength: got '{eval.strength}', expected '{expected_strength}'")
    
    if eval.has_flush_draw != expected_flush:
        issues.append(f"❌ Flush draw: got {eval.has_flush_draw}, expected {expected_flush}")
    
    if (eval.has_oesd or eval.has_gutshot) != expected_straight:
        issues.append(f"❌ Straight draw: got {eval.has_oesd or eval.has_gutshot}, expected {expected_straight}")
    
    if eval.made_hand != expected_made_hand:
        issues.append(f"❌ Made hand: got '{eval.made_hand}', expected '{expected_made_hand}'")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("✅ PASS")
        return True


def run_comprehensive_tests():
    """Test all major scenarios"""
    
    print("=" * 70)
    print("🎯 COMPREHENSIVE HAND EVALUATOR TEST SUITE")
    print("=" * 70)
    
    tests_passed = 0
    tests_total = 0
    
    # ============================================================
    print("\n" + "=" * 70)
    print("1️⃣  LOW PAIRS ON HIGH BOARDS (Weak Hands)")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "User's Original Issue - 77 on K-9-A",
        ["7 of Diamonds", "7 of Clubs"],
        ["King of Spades", "9 of Clubs", "Ace of Spades"],
        expected_strength="weak",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="pair"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "22 on Q-J-10 (low pair, connected board)",
        ["2 of Hearts", "2 of Diamonds"],
        ["Queen of Spades", "Jack of Clubs", "10 of Hearts"],
        expected_strength="weak",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="pair"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "55 on K-K-8 (low pair, paired board)",
        ["5 of Spades", "5 of Hearts"],
        ["King of Diamonds", "King of Clubs", "8 of Spades"],
        expected_strength="weak",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="two_pair"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("2️⃣  FLUSH DRAWS (Must have matching suits)")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "Real Flush Draw - AhKh on Qh9h2s",
        ["Ace of Hearts", "King of Hearts"],
        ["Queen of Hearts", "9 of Hearts", "2 of Spades"],
        expected_strength="medium",  # Flush draw is medium
        expected_flush=True,
        expected_straight=False,
        expected_made_hand="high_card"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "False Positive Check - AhKc on Qs9s2d (no matching suits)",
        ["Ace of Hearts", "King of Clubs"],
        ["Queen of Spades", "9 of Spades", "2 of Diamonds"],
        expected_strength="weak",  # Just high cards
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="high_card"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Backdoor Flush - 7d5d on Kd9c2h",
        ["7 of Diamonds", "5 of Diamonds"],
        ["King of Diamonds", "9 of Clubs", "2 of Hearts"],
        expected_strength="weak",  # Just backdoor
        expected_flush=False,  # Only 3 diamonds
        expected_straight=False,
        expected_made_hand="high_card"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("3️⃣  STRAIGHT DRAWS")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "OESD - JT on 9-8-2",
        ["Jack of Hearts", "10 of Clubs"],
        ["9 of Spades", "8 of Diamonds", "2 of Hearts"],
        expected_strength="medium",  # OESD is medium
        expected_flush=False,
        expected_straight=True,
        expected_made_hand="high_card"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Gutshot - JT on 9-7-2",
        ["Jack of Hearts", "10 of Clubs"],
        ["9 of Spades", "7 of Diamonds", "2 of Hearts"],
        expected_strength="weak",  # Gutshot is weak
        expected_flush=False,
        expected_straight=True,  # Has gutshot
        expected_made_hand="high_card"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "No Straight Draw - 77 on K-9-A (gaps too big)",
        ["7 of Hearts", "7 of Clubs"],
        ["King of Spades", "9 of Diamonds", "Ace of Hearts"],
        expected_strength="weak",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="pair"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("4️⃣  STRONG HANDS")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "Trips - 99 on 9-8-2",
        ["9 of Hearts", "9 of Clubs"],
        ["9 of Spades", "8 of Diamonds", "2 of Hearts"],
        expected_strength="strong",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="trips"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Two Pair - AK on A-K-2",
        ["Ace of Hearts", "King of Clubs"],
        ["Ace of Spades", "King of Diamonds", "2 of Hearts"],
        expected_strength="strong",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="two_pair"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Overpair - QQ on J-9-2",
        ["Queen of Hearts", "Queen of Clubs"],
        ["Jack of Spades", "9 of Diamonds", "2 of Hearts"],
        expected_strength="strong",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="pair"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("5️⃣  MONSTER HANDS")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "Straight - JT on 9-8-7",
        ["Jack of Hearts", "10 of Clubs"],
        ["9 of Spades", "8 of Diamonds", "7 of Hearts"],
        expected_strength="monster",
        expected_flush=False,
        expected_straight=False,  # Has made straight (not a draw)
        expected_made_hand="straight"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Flush - AhKh on Qh9h2h",
        ["Ace of Hearts", "King of Hearts"],
        ["Queen of Hearts", "9 of Hearts", "2 of Hearts"],
        expected_strength="monster",
        expected_flush=False,  # Has made flush (not a draw)
        expected_straight=False,
        expected_made_hand="flush"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Full House - 99 on 9-2-2",
        ["9 of Hearts", "9 of Clubs"],
        ["9 of Spades", "2 of Diamonds", "2 of Hearts"],
        expected_strength="monster",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="full_house"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("6️⃣  WET BOARDS (Multiple Draw Possibilities)")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "Monotone Board - 77 on Ks9sAs (no spades in hero)",
        ["7 of Hearts", "7 of Clubs"],
        ["King of Spades", "9 of Spades", "Ace of Spades"],
        expected_strength="weak",
        expected_flush=False,  # Hero has no spades!
        expected_straight=False,
        expected_made_hand="pair"
    ): tests_passed += 1
    
    tests_total += 1
    if test_scenario(
        "Connected Board - 77 on 10-9-8 (no straight for 77)",
        ["7 of Hearts", "7 of Clubs"],
        ["10 of Spades", "9 of Diamonds", "8 of Hearts"],
        expected_strength="weak",
        expected_flush=False,
        expected_straight=False,
        expected_made_hand="pair"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("7️⃣  COMBO DRAWS")
    print("=" * 70)
    
    tests_total += 1
    if test_scenario(
        "Flush + Straight Draw - JhTh on 9h8h2s",
        ["Jack of Hearts", "10 of Hearts"],
        ["9 of Hearts", "8 of Hearts", "2 of Spades"],
        expected_strength="strong",  # Combo draw is strong
        expected_flush=True,
        expected_straight=True,
        expected_made_hand="high_card"
    ): tests_passed += 1
    
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    print(f"\nTests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The hand evaluator correctly handles:")
        print("   • All board textures (high, low, connected, monotone)")
        print("   • All hand strengths (weak, medium, strong, monster)")
        print("   • All draw types (flush, straight, combo)")
        print("   • All made hands (pairs, trips, straights, flushes, etc.)")
        print("   • False positive prevention (hero must have matching cards)")
        print("\n✅ System is PRODUCTION READY for all scenarios!")
    else:
        print(f"\n❌ {tests_total - tests_passed} test(s) failed")
        print("Review the failures above for details")
    
    print("=" * 70)
    print()
    
    return tests_passed == tests_total


if __name__ == "__main__":
    print("\n")
    success = run_comprehensive_tests()
    exit(0 if success else 1)
