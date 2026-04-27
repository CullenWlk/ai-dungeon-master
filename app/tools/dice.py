import random

def roll_d20(modifier=0, mode="normal"):
    roll_1 = random.randint(1, 20)

    if mode == "advantage":
        roll_2 = random.randint(1, 20)
        chosen_roll = max(roll_1, roll_2)
    elif mode == "disadvantage":
        roll_2 = random.randint(1, 20)
        chosen_roll = min(roll_1, roll_2)
    else:
        roll_2 = None
        chosen_roll = roll_1

    total = chosen_roll + modifier

    return {
        "mode": mode,
        "roll": chosen_roll,
        "roll_1": roll_1,
        "roll_2": roll_2,
        "modifier": modifier,
        "total": total
    }