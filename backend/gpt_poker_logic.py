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


POKER_LOGIC_PROMPT = """You are an expert poker player and strategist. You will receive extracted data from a poker table and must make the optimal decision.

**Your job is to analyze the situation and recommend the best action with clear reasoning.**

**Game State Data:**
- Hero Position: {position}
- Hero Cards: {cards}
- Board Cards: {board}
- Pot Size: {pot}
- Street: {street}
- Blinds: {blinds}
- Action to Hero: {action_to_hero}
- Active Opponents: {opponents}
- Betting History: {history}

**Your Task:**
What is the most optimal play and why?

Consider:
- Hand strength vs likely opponent ranges
- Position advantage
- Pot odds and implied odds
- Opponent tendencies (VPIP if available)
- Board texture and draw possibilities
- Stack sizes and commitment
- Betting patterns

**Output Format (JSON only):**
{{
  "recommendation": {{
    "action": "Fold" or "Call" or "Check" or "Raise $4.50" or "Bet $3.00",
    "reasoning": "Clear 2-4 sentence explanation of why this is the optimal play based on hand strength, position, pot odds, opponent tendencies, and strategic considerations."
  }}
}}

**Rules:**
- Return ONLY valid JSON
- Keep reasoning concise but complete
- Include specific amounts for Raise/Bet actions
- Base decision on solid poker fundamentals"""


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
            Dictionary with decision and reasoning
        """
        try:
            logger.info("🧠 Sending extracted data to GPT-4o-mini for decision...")
            
            # Format opponent info
            opponents_info = []
            for pos, data in extracted_data.get('villain_positions', {}).items():
                vpip = data.get('vpip', 'N/A')
                stack = data.get('stack', 'N/A')
                bet = data.get('current_bet', '$0')
                opponents_info.append(f"{pos} (VPIP: {vpip}, Stack: {stack}, Bet: {bet})")
            
            opponents_str = ", ".join(opponents_info) if opponents_info else "None (heads-up or folded)"
            
            # Format the prompt with extracted data
            prompt = POKER_LOGIC_PROMPT.format(
                position=extracted_data.get('hero_position', 'Unknown'),
                cards=", ".join(extracted_data.get('hero_cards', [])),
                board=", ".join(extracted_data.get('board_cards', [])) if extracted_data.get('board_cards') else "Empty (preflop)",
                pot=extracted_data.get('pot_size_dollars', 'Unknown'),
                street=extracted_data.get('street', 'Unknown'),
                blinds=extracted_data.get('blinds', 'Unknown'),
                action_to_hero=extracted_data.get('action_to_hero', 'Unknown'),
                opponents=opponents_str,
                history=", ".join(extracted_data.get('betting_history', [])) if extracted_data.get('betting_history') else "No history available"
            )
            
            prompt += "\n\nMake your decision now. Return ONLY the JSON output, no markdown."
            
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
