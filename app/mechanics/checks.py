from app.character.sheet import get_skill_modifier
from app.tools.dice import roll_d20

def resolve_skill_check(sheet, skill_name, dc):
    modifier = get_skill_modifier(sheet, skill_name)
    roll_data = roll_d20(modifier)

    return {
        "roll_type": "skill_check",
        "skill": skill_name,
        "dc": dc,
        "roll": roll_data["roll"],
        "modifier": modifier,
        "total": roll_data["total"],
        "success": roll_data["total"] >= dc
    }