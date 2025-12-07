"""
GPT-4o-mini powered poker decision logic
Receives extracted data from Gemini and makes optimal poker decisions
"""

import os
import json
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("✅ OpenAI API key configured")
else:
    logger.warning("⚠️ OPENAI_API_KEY not set")
    client = None


POKER_LOGIC_PROMPT = """You are an expert poker mathematician and GTO strategist. You will receive extracted data from a poker table and must make the optimal decision.

**Your job is to calculate the 5 key metrics and recommend the best action based PURELY on mathematics.**

INPUT DATA FORMAT:
{
  "hero_position": "BTN|SB|BB|UTG|MP|CO",
  "hero_cards": ["A♠", "Q♠"],
  "board_cards": ["8♦", "6♦", "9♥"] or [],
  "pot_size_dollars": "10.50",
  "street": "preflop|flop|turn|river",
  "hero_stack": "150 BB",
  "villain_positions": {
    "BB": {"stack": "100 BB", "vpip": "28%", "current_bet": "$2.00"},
    "UTG": {"stack": "80 BB", "vpip": "18%", "current_bet": "$0"}
  },
  "action_to_hero": "$2.00 to call" or "No action - hero can check",
  "betting_history": ["UTG folds", "MP folds", "CO raises $2", "BTN (hero) ?"]
}

OUTPUT FORMAT (must be valid JSON):
{
  "recommendation": {
    "action": "Fold|Call|Check|Raise|Bet",
    "raise_amount_dollars": "$4.50" or "N/A",
    "pot_odds": "3:1" or "25%",
    "hand_equity": "45%",
    "implied_odds": "5:1" or "High/Medium/Low",
    "fold_equity": "35%",
    "expected_value": "+$2.10" or "-$0.75",
    "reasoning": "Brief 1-2 sentence mathematical explanation"
  }
}

CALCULATION GUIDELINES:

**1. POT ODDS**:
- Formula: (Amount to call) / (Pot after you call)
- Express as ratio or percentage
- Critical baseline for calling decisions

**2. HAND EQUITY**:
- Calculate hero's winning percentage vs villain's estimated range
- Consider position, action, board texture when constructing villain ranges
- Use combinatorics to remove impossible hands
- Tight players (low VPIP) = tighter ranges
- Loose players (high VPIP) = wider ranges

**3. IMPLIED ODDS**:
- Estimate additional chips you can win on future streets
- Factors:
  * Stack depth (deeper = higher implied odds)
  * Board texture (wet boards = lower implied odds) 
  * Drawing hands have high implied odds if hidden
  * Made hands have lower implied odds
- Express as ratio or High/Medium/Low

**4. FOLD EQUITY**:
- Estimate % villain folds to a bet/raise
- Factors:
  * Villain's VPIP (tight = folds more)
  * Pot size (small pots = easier folds)
  * Board texture (scary boards = more folds)
  * Bet sizing (bigger = more folds)
- Critical for bluffs and semi-bluffs

**5. EXPECTED VALUE**:
- For Call: EV = (Hand Equity × Pot) - Call Amount + Implied Odds adjustment
- For Bet/Raise: EV = (Fold Equity × Current Pot) + ((1 - Fold Equity) × ((Hand Equity × Final Pot) - Bet Amount))
- Choose action with highest EV
- Express in dollars

**DECISION LOGIC**:
- If EV(all actions) < 0 → Fold
- If Pot Odds < (Hand Equity + Implied Odds) → Profitable call
- If EV(Bet/Raise) > EV(Call) → Bet/Raise
- Blend GTO with exploitative adjustments based on VPIP

**IMPORTANT**:
- Base decisions on pure mathematics and the 5 metrics
- No guessing or assumptions beyond what's provided
- Show your mathematical work in reasoning
- Be precise with percentages and dollar amounts

Return ONLY valid JSON, no markdown, no extra text."""


class GPTPokerLogic:
    """Poker decision engine using GPT-4o-mini"""
    
    def __init__(self):
        """Initialize GPT client"""
        if not client:
            raise ValueError("OpenAI API key not configured")
        logger.info("✅ GPT-4o-mini poker logic initialized")
    
    def make_decision(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make poker decision using GPT-4o-mini
        
        Args:
            extracted_data: Dictionary with poker table data extracted by Gemini
            
        Returns:
            Dictionary with decision and 5 metrics
        """
        try:
            logger.info("🧠 Sending extracted data to GPT-4o-mini for decision...")
            
            # Format the prompt with extracted data
            prompt = f"""{POKER_LOGIC_PROMPT}

INPUT DATA:
{json.dumps(extracted_data, indent=2)}

Make your decision now. Return ONLY the JSON output, no markdown."""
            
            # Call GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap!
                messages=[
                    {"role": "system", "content": "You are a poker mathematics expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Balance between deterministic and creative
                max_tokens=1000,
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            
            # Parse response
            decision_text = response.choices[0].message.content.strip()
            decision = json.loads(decision_text)
            
            logger.info(f"✅ GPT decision: {decision['recommendation']['action']}")
            
            return {
                "success": True,
                "decision": decision
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse GPT response as JSON: {e}")
            logger.error(f"Raw response: {decision_text[:500]}")
            return {
                "success": False,
                "error": "Failed to parse decision response",
                "raw_response": decision_text[:500]
            }
            
        except Exception as e:
            logger.error(f"❌ GPT decision error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
