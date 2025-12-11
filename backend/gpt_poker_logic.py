"""
GPT-4o-mini powered poker decision logic
Receives extracted data from Gemini and makes optimal poker decisions
Uses Gemini's detailed extraction focus for comprehensive analysis
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


# Enhanced prompt emphasizing visual extraction details
POKER_LOGIC_PROMPT = """You are an expert poker player and strategist. Gemini has extracted visual data from a poker table. Your job is to make the optimal decision based on this detailed information.

**EXTRACTED GAME STATE:**

**Hero Context:**
- Position: {position}
- Cards: {cards}
- Stack: {hero_stack}
- Blinds: {blinds}

**Board:**
- Street: {street}
- Community Cards: {board}

**Pot & Action:**
- Pot Size: {pot}
- Action to Hero: {action_to_hero}
- Observed Action: {action_observed}

**Active Opponents (ONLY players with visible cards):**
{opponents}

**Folded Players:**
{folded_players}

**Betting History:**
{history}

---

## YOUR ANALYSIS REQUIREMENTS:

**1. ACTION CONTEXT - CRITICAL:**
- Is this an initial raise, 3-bet, 4-bet, or squeeze?
- How many players saw the flop vs how many are active now?
- What does the bet size tell you about opponent's range?
- Are you facing aggression or can you see the flop cheaply?

**2. HAND STRENGTH vs RANGE:**
- What is your absolute hand strength?
- What is your hand strength vs opponent's likely raising/3-betting/betting range?
- How does your hand play vs the number of active opponents?
- Position consideration: How does {position} affect your range advantage?

**3. POT ODDS & IMPLIED ODDS:**
- Calculate actual pot odds based on bet you're facing
- Consider implied odds with drawing hands
- Evaluate reverse implied odds with vulnerable made hands
- Stack-to-pot ratio (SPR) considerations

**4. NUMBER OF OPPONENTS:**
- Heads-up vs multi-way dramatically changes strategy
- Check folded_players list - don't count them!
- With more active opponents, tighten ranges significantly
- Speculative hands lose value multi-way

**5. OPPONENT TENDENCIES:**
- VPIP stats if available
- Bet sizing patterns
- Position-based tendencies

**6. BOARD TEXTURE** (post-flop):
- Wet or dry?
- Draw possibilities?
- How does your hand interact with the board?

---

## DECISION-MAKING RULES:

**For 3-bets:**
- Tighten range significantly vs 3-bets
- Suited connectors become folds vs 3-bets (not enough implied odds)
- Strong broadway hands increase in value
- Position matters less when facing 3-bet

**For Initial Raises:**
- Wider calling range from late position
- Speculative hands (suited connectors, small pairs) playable with position
- Stronger hands can 3-bet for value or protection

**For Multi-way Pots:**
- Dramatically tighten continuing range
- Drawing hands need better price
- Made hands with little room to improve often fold

**For Heads-up:**
- Wider ranges acceptable
- Position is king
- More room for creative play

**If Action is Unclear:**
- State this explicitly in your reasoning
- Make best decision based on pot size and visible information
- Note any assumptions you're making

---

## OUTPUT FORMAT (JSON only):

{{
  "recommendation": {{
    "action": "Fold" or "Call $X.XX" or "Check" or "Raise to $X.XX" or "Bet $X.XX",
    "reasoning": "Detailed explanation: [Describe the action situation - initial raise/3-bet/etc]. With [hand] in {position} position facing [describe specific action], against [number] active opponents, the optimal play is [action] because: [2-4 sentences covering hand strength vs range, pot odds, position advantage, and strategic context including whether this is a 3-bet situation]."
  }}
}}

**CRITICAL RULES:**
- Return ONLY valid JSON
- Mention the ACTION CONTEXT in reasoning (3-bet, initial raise, etc.)
- Note number of ACTIVE opponents (exclude folded players)
- Explain pot odds if calling/folding decision
- Base decision on ACTUAL observed action, not assumptions
- If action unclear, state it and explain your assumptions"""


class GPTPokerLogic:
    """Poker decision engine using GPT-4o-mini with detailed extraction focus"""
    
    def __init__(self):
        """Initialize GPT client"""
        if not client:
            raise ValueError("OpenAI API key not configured")
        logger.info("✅ GPT-4o-mini poker logic initialized (detailed extraction focus)")
    
    def make_decision(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make poker decision using GPT-4o-mini
        
        Args:
            extracted_data: Dictionary with poker table data extracted by Gemini
            
        Returns:
            Dictionary with decision and reasoning
        """
        try:
            logger.info("🧠 Sending extracted data to GPT-4o-mini for decision...")
            
            # Format opponent info from extracted data
            opponents_info = []
            
            # Try to get active_players (new format)
            active_players = extracted_data.get('active_players', [])
            if active_players:
                for player in active_players:
                    pos = player.get('position', 'Unknown')
                    name = player.get('name', 'Unknown')
                    vpip = player.get('vpip', 'N/A')
                    stack = player.get('stack', 'N/A')
                    bet = player.get('current_bet', '$0')
                    folded = player.get('has_folded', False)
                    if not folded:
                        opponents_info.append(f"- {pos}: {name} (VPIP: {vpip}, Stack: {stack}, Current Bet: {bet})")
            else:
                # Fallback to villain_positions (old format)
                for pos, data in extracted_data.get('villain_positions', {}).items():
                    name = data.get('player_name', 'Unknown')
                    vpip = data.get('vpip', 'N/A')
                    stack = data.get('stack', 'N/A')
                    bet = data.get('current_bet', '$0')
                    folded = data.get('has_folded', False)
                    if not folded:
                        opponents_info.append(f"- {pos}: {name} (VPIP: {vpip}, Stack: {stack}, Current Bet: {bet})")
            
            opponents_str = "\n".join(opponents_info) if opponents_info else "None visible (may be heads-up, or all others folded)"
            
            # Get folded players list
            folded_players = extracted_data.get('folded_players', [])
            folded_str = ", ".join(folded_players) if folded_players else "None or unclear from extraction"
            
            # Get action observed
            action_observed = extracted_data.get('action_observed', 'Action sequence unclear from visual extraction')
            
            # Format the prompt with extracted data
            prompt = POKER_LOGIC_PROMPT.format(
                position=extracted_data.get('hero_position', 'Unknown'),
                cards=", ".join(extracted_data.get('hero_cards', [])) or "Unknown",
                hero_stack=extracted_data.get('hero_stack', 'Unknown'),
                board=", ".join(extracted_data.get('board_cards', [])) if extracted_data.get('board_cards') else "Empty (preflop)",
                pot=extracted_data.get('pot_size_dollars', 'Unknown'),
                street=extracted_data.get('street', 'Unknown'),
                blinds=extracted_data.get('blinds', 'Unknown'),
                action_to_hero=extracted_data.get('action_to_hero', 'Unknown'),
                action_observed=action_observed,
                opponents=opponents_str,
                folded_players=folded_str,
                history=", ".join(extracted_data.get('betting_history', [])) if extracted_data.get('betting_history') else "No history extracted from image"
            )
            
            prompt += "\n\nMake your decision now. Return ONLY the JSON output, no markdown."
            
            # Call GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a poker GTO expert and mathematics specialist. Always respond with valid JSON only. Pay special attention to action context (3-bets vs initial raises)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
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
