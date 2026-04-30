SKILL_ABILITIES = {
    "acrobatics": "dexterity",
    "animal_handling": "wisdom",
    "arcana": "intelligence",
    "athletics": "strength",
    "deception": "charisma",
    "history": "intelligence",
    "insight": "wisdom",
    "intimidation": "charisma",
    "investigation": "intelligence",
    "medicine": "wisdom",
    "nature": "intelligence",
    "perception": "wisdom",
    "performance": "charisma",
    "persuasion": "charisma",
    "religion": "intelligence",
    "sleight_of_hand": "dexterity",
    "stealth": "dexterity",
    "survival": "wisdom",
}


def ability_modifier(score):
    return (score - 10) // 2


def calculate_skills(abilities, proficient_skills, proficiency_bonus):
    skills = {}

    for skill, ability in SKILL_ABILITIES.items():
        modifier = ability_modifier(abilities.get(ability, 10))

        if skill in proficient_skills:
            modifier += proficiency_bonus

        skills[skill] = modifier

    return skills