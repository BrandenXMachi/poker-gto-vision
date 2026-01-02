# Flop → T/R Context Inheritance System

## Overview
Implemented complete context inheritance from Flop mode to Turn/River mode, allowing seamless progression through streets while retaining card information from previous analysis.

## Changes Implemented

### Frontend (page.tsx)

1. **Enhanced Context Interface**
   - Extended `inheritedContext` to support Flop → T/R data
   - Added fields: `heroCards`, `flopCards`, `flopAction`, `flopRecommendation`
   - Supports both Preflop → Flop and Flop → T/R transitions

2. **Updated continueToTR() Function**
   - Saves hero's 2 hole cards from flop analysis
   - Saves first 3 board cards (flop only)
   - Passes positional info (IP/OOP, villain position)
   - Stores flop action context for future enhancements

3. **Enhanced captureAndAnalyze() for T/R Mode**
   - Checks for inherited context from Flop mode
   - Passes `hero_cards` and `flop_cards` as JSON to backend
   - Sends positional and action context
   - Logs context transmission for debugging

4. **New UI: T/R Context Indicator**
   - Shows inherited card information when context exists
   - Displays: Hero cards, Flop cards, Position info
   - Includes "Manual Input" button to reset context
   - Explains that Gemini will only extract turn/river + pot/call

### Backend

#### main.py

1. **New Form Parameters**
   - `hero_cards`: JSON string of 2 hero cards from Flop
   - `flop_cards`: JSON string of 3 flop cards
   - `flop_action`: Preflop action context
   
2. **Enhanced T/R Mode Handler**
   - Parses JSON context from frontend
   - Validates and logs received context
   - Passes context to TurnRiverAnalyzer

#### turn_river_analyzer.py

1. **Updated analyze() Signature**
   - Added optional parameters: `hero_cards`, `flop_cards`, `hero_position`, `villain_position`, `flop_action`
   - Detects when context is available
   - Switches between full vs partial extraction

2. **New _build_partial_prompt() Method**
   - Simplified Gemini prompt when cards are known
   - Only extracts: NEW cards (turn/river), pot size, call amount
   - Explicitly tells Gemini NOT to extract hero/flop cards
   - Reduces AI workload and improves accuracy

3. **Smart Card Combination Logic**
   - When context exists: combines `flop_cards` + `new_cards` from Gemini
   - When no context: uses full extraction
   - Validates final card counts (2 hero, 4-5 board)

4. **Maintains Full Functionality**
   - All calculation methods work with both modes
   - No changes to decision logic
   - Same output format regardless of extraction method

## User Experience

### Workflow: Preflop → Flop → Turn/River

1. **Preflop Analysis**
   - User analyzes preflop decision with JJ
   - Gets recommendation: "Call" or "3-bet"
   - Clicks "Continue to Flop"

2. **Flop Analysis**
   - Context indicator shows preflop position/action
   - User captures flop image
   - Gemini extracts: hero cards + 3 flop cards
   - Gets flop GTO recommendation
   - Clicks "Continue to T/R"

3. **Turn/River Analysis** (NEW!)
   - **Context indicator shows:** Hero's cards + Flop cards
   - **Gemini only extracts:** Turn/river card + pot/call
   - **System combines:** Known flop + new card(s) = complete board
   - **Result:** Faster, more accurate analysis

### Benefits

1. **Reduced AI Workload**
   - Gemini doesn't re-extract known information
   - Simpler prompt = faster response
   - Lower chance of card misidentification

2. **Continuity Through Streets**
   - Cards stay consistent across street transitions
   - No risk of Gemini "seeing different cards"
   - Natural poker hand progression

3. **Flexible Usage**
   - Can use T/R mode standalone (full extraction)
   - Can use after Flop (partial extraction)
   - "Manual Input" button resets to standalone mode

4. **Same Quality Decisions**
   - All pot odds, equity, EV calculations unchanged
   - Decision logic remains identical
   - Just changes HOW cards are identified

## Technical Details

### Frontend → Backend Data Flow

```javascript
// Frontend sends:
formData.append('hero_cards', JSON.stringify(['Ace of Spades', 'King of Hearts']))
formData.append('flop_cards', JSON.stringify(['Queen of Hearts', 'Jack of Diamonds', '10 of Clubs']))
```

```python
# Backend receives and parses:
hero_cards_list = json.loads(hero_cards)  # ['Ace of Spades', 'King of Hearts']
flop_cards_list = json.loads(flop_cards)  # ['Queen of Hearts', 'Jack of Diamonds', '10 of Clubs']
```

### Gemini Extraction Logic

**With Context (Partial Extraction):**
```
Gemini extracts: ["8 of Diamonds"]  # Just the turn card
System combines: ['Q♥', 'J♦', '10♣'] + ['8♦'] = ['Q♥', 'J♦', '10♣', '8♦']
Final hero cards: ['A♠', 'K♥']  # From context
```

**Without Context (Full Extraction):**
```
Gemini extracts: 
  hero_cards: ['Ace of Spades', 'King of Hearts']
  board_cards: ['Queen of Hearts', 'Jack of Diamonds', '10 of Clubs', '8 of Diamonds']
```

### Error Handling

- Validates hero cards = 2
- Validates board cards = 4 or 5
- Graceful fallback if context parsing fails
- Logs all context usage for debugging

## Future Enhancements

1. **Positional Adjustments**
   - Use `hero_position` (IP/OOP) for equity adjustments
   - Use `villain_position` for range estimates
   - Tighter/looser ranges based on position

2. **Action History**
   - Track betting patterns through streets
   - Adjust fold equity based on aggression
   - Better bluff-catching decisions

3. **Multi-Street EV**
   - Calculate EV considering all streets
   - Account for implied odds from previous action
   - More sophisticated pot odds calculations

## Testing

Recommended test flow:
1. Start with Preflop analysis (any hand)
2. Continue to Flop (observe context indicator)
3. Capture flop image, get recommendation
4. Continue to T/R (observe flop context indicator)
5. Capture turn image
6. Verify: hero cards + flop cards correct, only turn card extracted

## Summary

This implementation provides seamless multi-street analysis while maintaining data consistency and reducing AI extraction complexity. The system is backwards compatible - T/R mode works standalone OR with Flop context, giving users maximum flexibility.
