from app.character.sheet import get_skill_modifier
from app.tools.dice import roll_d20

def resolve_skill_check(sheet, skill_name, dc, mode="normal"):
    modifier = get_skill_modifier(sheet, skill_name)
    roll_data = roll_d20(modifier, mode)

    return {
        "roll_type": "skill_check",
        "skill": skill_name,
        "dc": dc,
        "mode": roll_data["mode"],
        "roll": roll_data["roll"],
        "roll_1": roll_data["roll_1"],
        "roll_2": roll_data["roll_2"],
        "modifier": modifier,
        "total": roll_data["total"],
        "success": roll_data["total"] >= dc
    }