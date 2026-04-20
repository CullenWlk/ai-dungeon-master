import json

def build_action_prompt(player_text):
    return f"""
You are acting as the DM adjudication layer for a fantasy RPG.

Read the player's action and decide whether:
1. simple narration is enough
2. a skill check is required

If a skill check is required, return JSON only in this format:

{{
  "action_type": "request_check",
  "display_text": "Make a Stealth check.",
  "roll_type": "skill_check",
  "skill": "stealth",
  "dc": 13,
  "reason": "The player is trying to move quietly past an alert guard."
}}

If no roll is required, return JSON only in this format:

{{
  "action_type": "narration",
  "display_text": "Brief two sentence narration text here."
}}

Player action:
"{player_text}"
""".strip()

def parse_action_response(text):
    return json.loads(text)