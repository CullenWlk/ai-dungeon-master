import random

def roll_d20(modifier=0):
    roll = random.randint(1, 20)
    total = roll + modifier

    return {
        "roll": roll,
        "modifier": modifier,
        "total": total
    }