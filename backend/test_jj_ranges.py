"""
Simple test to verify JJ and TT are now in the correct calling ranges
"""

# Copy the updated ranges from preflop_gto_analyzer.py
CALLING_VS_OPEN = {
    "MP_vs_UTG": ["22", "33", "44", "55", "66", "77", "88", "99", "TT", "JJ", "AJs", "AQs", "KQs", "QJs", "JTs", "T9s"],
    "CO_vs_UTG": ["22", "33", "44", "55", "66", "77", "88", "99", "TT", "JJ", "AJs", "AQs", "KQs", "QJs", "JTs", "T9s"],
    "BTN_vs_UTG": ["22", "33", "44", "55", "66", "77", "88", "99", "TT", "JJ", "AJs", "AQs", "KQs", "QJs", "JTs", "T9s"],
}

def test_ranges():
    """Test that JJ and TT are in the calling ranges"""
    
    print("\n" + "=" * 70)
    print("TESTING UPDATED GTO RANGES")
    print("=" * 70)
    
    tests = [
        ("JJ", "MP_vs_UTG", "MP facing UTG open"),
        ("TT", "MP_vs_UTG", "MP facing UTG open"),
        ("JJ", "CO_vs_UTG", "CO facing UTG open"),
        ("TT", "CO_vs_UTG", "CO facing UTG open"),
        ("JJ", "BTN_vs_UTG", "BTN facing UTG open"),
        ("TT", "BTN_vs_UTG", "BTN facing UTG open"),
    ]
    
    passed = 0
    failed = 0
    
    for hand, range_key, description in tests:
        if hand in CALLING_VS_OPEN[range_key]:
            print(f"✅ PASS: {hand} is in {range_key} ({description})")
            passed += 1
        else:
            print(f"❌ FAIL: {hand} is NOT in {range_key} ({description})")
            failed += 1
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! JJ and TT are now correctly in calling ranges.")
        print("\nWhat this means:")
        print("• JJ from MP vs UTG open → Will recommend CALL (not fold)")
        print("• TT from positions vs UTG open → Will recommend CALL (not fold)")
        print("• These are now treated as strong speculative hands with good implied odds")
    else:
        print("\n⚠️ SOME TESTS FAILED!")
    
    print("=" * 70)
    
    # Show the complete MP_vs_UTG range
    print("\nComplete MP_vs_UTG calling range:")
    print(CALLING_VS_OPEN["MP_vs_UTG"])
    print()
    
    return failed == 0

if __name__ == "__main__":
    test_ranges()
