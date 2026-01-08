"""
Test to verify equity calculation fix
Tests the specific case: 6♦5♦ on 8♣A♥3♠9♦ = 4 outs (gutshot) = 8.7% equity
"""

import sys
sys.path.append('.')

from turn_river_analyzer import TurnRiverAnalyzer
from hand_evaluator import evaluate_hand


def test_gutshot_equity():
    """Test 4-out gutshot shows 8.7% equity (not 30%)"""
    print("\n" + "="*60)
    print("TEST: Gutshot Equity Calculation")
    print("="*60)
    
    # Your specific hand
    hero_cards = ["6 of Diamonds", "5 of Diamonds"]
    board_cards = ["8 of Clubs", "Ace of Hearts", "3 of Spades", "9 of Diamonds"]
    
    print(f"\nHero: {hero_cards}")
    print(f"Board (Turn): {board_cards}")
    print(f"\nExpected: 4-out gutshot (need a 7 for straight)")
    print(f"Expected equity: 4/46 = 8.7%")
    
    # Evaluate hand
    evaluation = evaluate_hand(hero_cards, board_cards)
    
    print(f"\n✅ Hand evaluation:")
    print(f"   Made hand: {evaluation.made_hand}")
    print(f"   Description: {evaluation.description}")
    print(f"   Strength: {evaluation.strength}")
    print(f"   Has gutshot: {evaluation.has_gutshot}")
    print(f"   Straight draw outs: {evaluation.straight_draw_outs}")
    
    # Calculate equity using the analyzer's method
    analyzer = TurnRiverAnalyzer()
    outs = evaluation.straight_draw_outs
    equity = analyzer._calculate_equity(
        street="turn",
        outs=outs,
        hand_strength=evaluation.strength,
        evaluation=evaluation
    )
    
    print(f"\n📊 Equity calculation:")
    print(f"   Outs: {outs}")
    print(f"   Calculated equity: {equity:.1f}%")
    
    expected_equity = (4 / 46) * 100  # 8.7%
    
    if abs(equity - expected_equity) < 0.1:
        print(f"\n✅ PASS: Equity is {equity:.1f}% (expected ~8.7%)")
        return True
    else:
        print(f"\n❌ FAIL: Equity is {equity:.1f}% (expected ~8.7%)")
        return False


def test_flush_draw_equity():
    """Test 9-out flush draw shows 19.6% equity"""
    print("\n" + "="*60)
    print("TEST: Flush Draw Equity Calculation")
    print("="*60)
    
    hero_cards = ["Ace of Hearts", "King of Hearts"]
    board_cards = ["Queen of Hearts", "Jack of Hearts", "3 of Clubs", "2 of Spades"]
    
    print(f"\nHero: {hero_cards}")
    print(f"Board (Turn): {board_cards}")
    print(f"\nExpected: 9-out flush draw")
    print(f"Expected equity: 9/46 = 19.6%")
    
    evaluation = evaluate_hand(hero_cards, board_cards)
    
    print(f"\n✅ Hand evaluation:")
    print(f"   Made hand: {evaluation.made_hand}")
    print(f"   Has flush draw: {evaluation.has_flush_draw}")
    print(f"   Flush draw outs: {evaluation.flush_draw_outs}")
    
    analyzer = TurnRiverAnalyzer()
    
    # Count outs properly (includes flush draw)
    outs = evaluation.flush_draw_outs
    
    equity = analyzer._calculate_equity(
        street="turn",
        outs=outs,
        hand_strength=evaluation.strength,
        evaluation=evaluation
    )
    
    print(f"\n📊 Equity calculation:")
    print(f"   Outs: {outs}")
    print(f"   Calculated equity: {equity:.1f}%")
    
    expected_equity = (9 / 46) * 100  # 19.6%
    
    if abs(equity - expected_equity) < 0.1:
        print(f"\n✅ PASS: Equity is {equity:.1f}% (expected ~19.6%)")
        return True
    else:
        print(f"\n❌ FAIL: Equity is {equity:.1f}% (expected ~19.6%)")
        return False


def test_made_hand_no_outs():
    """Test made hand with no outs uses showdown equity"""
    print("\n" + "="*60)
    print("TEST: Made Hand (No Outs) Equity Calculation")
    print("="*60)
    
    hero_cards = ["King of Diamonds", "King of Hearts"]
    board_cards = ["9 of Spades", "5 of Clubs", "2 of Hearts", "8 of Diamonds"]
    
    print(f"\nHero: {hero_cards}")
    print(f"Board (Turn): {board_cards}")
    print(f"\nExpected: Pocket Kings (strong hand, no draws)")
    print(f"Expected equity: ~70% (showdown equity vs opponent)")
    
    evaluation = evaluate_hand(hero_cards, board_cards)
    
    print(f"\n✅ Hand evaluation:")
    print(f"   Made hand: {evaluation.made_hand}")
    print(f"   Description: {evaluation.description}")
    print(f"   Strength: {evaluation.strength}")
    
    analyzer = TurnRiverAnalyzer()
    
    # Should have 0 outs (no draws with pocket pair on rainbow board)
    outs = 0
    
    equity = analyzer._calculate_equity(
        street="turn",
        outs=outs,
        hand_strength=evaluation.strength,
        evaluation=evaluation
    )
    
    print(f"\n📊 Equity calculation:")
    print(f"   Outs: {outs}")
    print(f"   Calculated equity: {equity:.1f}%")
    
    # Should use showdown equity for "strong" hand = 70%
    if equity == 70.0:
        print(f"\n✅ PASS: Equity is {equity:.1f}% (showdown equity for strong hand)")
        return True
    else:
        print(f"\n❌ FAIL: Equity is {equity:.1f}% (expected 70% for strong made hand)")
        return False


def test_oesd_equity():
    """Test 8-out OESD shows 17.4% equity"""
    print("\n" + "="*60)
    print("TEST: OESD (Open-Ended Straight Draw) Equity")
    print("="*60)
    
    hero_cards = ["Jack of Spades", "Ten of Hearts"]
    board_cards = ["Queen of Diamonds", "9 of Clubs", "2 of Hearts", "4 of Spades"]
    
    print(f"\nHero: {hero_cards}")
    print(f"Board (Turn): {board_cards}")
    print(f"\nExpected: OESD (need K or 8 for straight)")
    print(f"Expected equity: 8/46 = 17.4%")
    
    evaluation = evaluate_hand(hero_cards, board_cards)
    
    print(f"\n✅ Hand evaluation:")
    print(f"   Made hand: {evaluation.made_hand}")
    print(f"   Has OESD: {evaluation.has_oesd}")
    print(f"   Straight draw outs: {evaluation.straight_draw_outs}")
    
    analyzer = TurnRiverAnalyzer()
    outs = evaluation.straight_draw_outs
    
    equity = analyzer._calculate_equity(
        street="turn",
        outs=outs,
        hand_strength=evaluation.strength,
        evaluation=evaluation
    )
    
    print(f"\n📊 Equity calculation:")
    print(f"   Outs: {outs}")
    print(f"   Calculated equity: {equity:.1f}%")
    
    expected_equity = (8 / 46) * 100  # 17.4%
    
    if abs(equity - expected_equity) < 0.1:
        print(f"\n✅ PASS: Equity is {equity:.1f}% (expected ~17.4%)")
        return True
    else:
        print(f"\n❌ FAIL: Equity is {equity:.1f}% (expected ~17.4%)")
        return False


if __name__ == "__main__":
    print("\n🧪 EQUITY CALCULATION FIX - TEST SUITE")
    print("="*60)
    print("Testing that draw equity is calculated correctly")
    print("(Not using max() of draw equity vs showdown equity)")
    
    results = []
    
    # Run all tests
    results.append(("Gutshot (4 outs)", test_gutshot_equity()))
    results.append(("Flush Draw (9 outs)", test_flush_draw_equity()))
    results.append(("Made Hand (0 outs)", test_made_hand_no_outs()))
    results.append(("OESD (8 outs)", test_oesd_equity()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Equity calculation is now correct.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review.")
        sys.exit(1)
