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
/no_think
A check is currently pending.

Pending check:
- roll_type: {pending_check['roll_type']}
- skill: {pending_check['skill']}
- dc: {pending_check['dc']}
- mode: {pending_check.get('mode', 'normal')}
- reason: {pending_check['reason']}

The player replied:
"{player_text}"

This phase is NOT for narration. It is only for ruling on the pending check.

The player may be:
1. arguing for a different skill
2. arguing for advantage
3. arguing against disadvantage
4. arguing that no roll should be required
5. changing their intended approach

Return JSON only in one of these forms:

If the check still happens, with or without changes:

{{
  "action_type": "modify_check",
  "display_text": "Short DM ruling shown to the player.",
  "skill": "stealth",
  "dc": 13,
  "mode": "normal",
  "reason": "Updated reason for the check."
}}

If the roll should be cancelled and the action should return to narration:

{{
  "action_type": "cancel_check",
  "display_text": "Short DM ruling shown to the player.",
  "revised_action": "One sentence describing what the player is now actually trying to do."
}}

Rules:
- Do not narrate the outcome of the scene.
- Only give a short DM ruling.
- mode must be one of: "normal", "advantage", or "disadvantage".
- Use advantage if the player's argument gives them a clear tactical, environmental, or roleplay benefit.
- Use disadvantage if the circumstances clearly hinder the player.
- Use normal if neither side has a strong reason.
- If no roll is needed anymore, use cancel_check.
- Return valid JSON only.
- Do not wrap JSON in markdown.
""".strip()

def parse_pending_response(text):
    return json.loads(text)