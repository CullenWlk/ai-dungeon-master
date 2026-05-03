import json

def build_action_prompt(player_text):
    return f"""
/no_think
You are acting as the DM adjudication layer for a fantasy RPG.

Read the player's action and decide whether:
1. simple narration is enough
2. a skill check is required

If a skill check is required, return JSON only in this format (if the player is attempting to lie or do anything that could be considered persuasion, they must make a check. If the player is looking for something they must either make a perception or investigation check depending on if they are just looking or actively searching with their hands as well.):

{{
  "action_type": "request_check",
  "display_text": "Make a Stealth check.",
  "roll_type": "skill_check",
  "skill": "stealth",
  "dc": 13,
  "reason": "The player is trying to move quietly past an alert guard.",
  "mode": "mode must be one of: "normal", "advantage", or "disadvantage". Use advantage when circumstances strongly favor the player. Use disadvantage when circumstances strongly hinder the player. Otherwise use normal."
}}

If no roll is required, return JSON only in this format:

{{
  "action_type": "narration",
  "location": "2-sentence description of player's current location. If they are in a named location, always include the name of the location, what town or city it is in, along with the description of where the player is within it."
  "interaction_context": "2-sentence description of the previous things said in a conversation with a npc and their actions. Simply say 'none' here if there is no npc interaction happening currently."
}}

Rules:
- do not include narration text in the narration response
- do not wrap JSON in markdown code fences
- return valid JSON only

Player action:
"{player_text}"
""".strip()

def parse_action_response(text):
    return json.loads(text)