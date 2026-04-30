import json
from pathlib import Path


def load_character_sheet(path=None):
    if path is not None:
        sheet_path = Path(path)
    else:
        session_path = Path("app/data/current_character_sheet.json")
        default_path = Path("app/data/character_sheet.json")
        sheet_path = session_path if session_path.exists() else default_path

    with open(sheet_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_skill_modifier(sheet, skill_name):
    return sheet.get("skills", {}).get(skill_name.lower(), 0)