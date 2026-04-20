import json

def is_roll_command(text):
    normalized = text.lower().strip()
    return normalized in {
        "roll",
        "i roll",
        "okay i roll",
        "fine, i roll",
        "fine i roll",
        "go ahead",
        "do it",
        "rolling"
    }

def build_pending_prompt(player_text, pending_check):
    return f"""
A check is currently pending.

Pending check:
- roll_type: {pending_check['roll_type']}
- skill: {pending_check['skill']}
- dc: {pending_check['dc']}
- reason: {pending_check['reason']}

The player replied:
"{player_text}"

Decide whether:
1. the check stays the same
2. the skill should change
3. the player is changing approach entirely

Return JSON only in one of these forms:

{{
  "action_type": "modify_check",
  "display_text": "text shown to player",
  "skill": "stealth",
  "dc": 13
}}

or

{{
  "action_type": "change_approach",
  "display_text": "text shown to player"
}}
""".strip()

def parse_pending_response(text):
    return json.loads(text)