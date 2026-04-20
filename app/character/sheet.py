import json

def load_character_sheet(path="app/data/character_sheet.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def get_skill_modifier(sheet, skill_name):
    return sheet["skills"].get(skill_name, 0)