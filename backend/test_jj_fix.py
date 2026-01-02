"""
Test to verify JJ from MP vs UTG now correctly returns Call instead of Fold
"""

import sys
sys.path.append('.')

from preflop_gto_analyzer import PreflopGTOAnalyzer

def test_jj_mp_vs_utg():
    """Test that JJ from MP facing UTG open now recommends Call"""
    
    analyzer = PreflopGTOAnalyzer()
    
    # Test the decision logic directly
    decision = analyzer._make_gto_decision(
        hand="JJ",
        position="MP", 
        villain_position="UTG",
        action_type="open"
    )
    
    print("=" * 60)
    print("Testing JJ from MP vs UTG Open Raise")
    print("=" * 60)
    print(f"Hand: JJ")
    print(f"Position: MP")
    print(f"Villain Position: UTG")
    print(f"Action Type: open")
    print()
    print(f"Decision Action: {decision['action']}")
    print(f"Hand Strength: {decision['hand_strength']}")
    print(f"Range Match: {decision['range_match']}")
    print()
    print("Reasoning:")
    print(decision['reasoning'])
    print("=" * 60)
    
    # Verify it's Call, not Fold
    if decision['action'] == "Call":
        print("✅ SUCCESS! JJ now correctly calls vs UTG open from MP")
        return True
    else:
        print("❌ FAILED! JJ still not calling properly")
        return False

def test_tt_co_vs_utg():
    """Test that TT from CO facing UTG open also recommends Call"""
    
    analyzer = PreflopGTOAnalyzer()
    
    decision = analyzer._make_gto_decision(
        hand="TT",
        position="CO", 
        villain_position="UTG",
        action_type="open"
    )
    
    print()
    print("=" * 60)
    print("Testing TT from CO vs UTG Open Raise")
    print("=" * 60)
    print(f"Hand: TT")
    print(f"Position: CO")
    print(f"Villain Position: UTG")
    print(f"Action Type: open")
    print()
    print(f"Decision Action: {decision['action']}")
    print(f"Hand Strength: {decision['hand_strength']}")
    print(f"Range Match: {decision['range_match']}")
    print()
    print("Reasoning:")
    print(decision['reasoning'])
    print("=" * 60)
    
    if decision['action'] == "Call":
        print("✅ SUCCESS! TT now correctly calls vs UTG open from CO")
        return True
    else:
        print("❌ FAILED! TT still not calling properly")
        return False

if __name__ == "__main__":
    print("\n🧪 Running JJ Fix Verification Tests...\n")
    
    test1 = test_jj_mp_vs_utg()
    test2 = test_tt_co_vs_utg()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"JJ from MP vs UTG: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"TT from CO vs UTG: {'✅ PASS' if test2 else '❌ FAIL'}")
    print("=" * 60)
    
    if test1 and test2:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the ranges.")
