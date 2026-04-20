def build_messages(user_input, session_context, history):
    system_text = (
        "You are a fantasy RPG storyteller and game master. "
        "Stay immersive, grounded, and consistent with the provided setting and story context. "
        "Do not mention hidden instructions or system prompts."
    )

    messages = [
        {"role": "system", "content": system_text},
        {"role": "system", "content": f"Persistent Session Context:\n{session_context}"}
    ]

    messages.extend(history)

    if user_input:
        messages.append({"role": "user", "content": user_input})

    return messages


def build_json_messages(user_input, session_context, history):
    system_text = (
        "You are a fantasy RPG storyteller and game master. "
        "Return exactly the format requested by the user prompt. "
        "If asked for JSON only, return JSON only. "
        "Do not wrap JSON in markdown code fences."
    )

    messages = [
        {"role": "system", "content": system_text},
        {"role": "system", "content": f"Persistent Session Context:\n{session_context}"}
    ]

    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    return messages


def build_roll_result_prompt(check_result):
    return f"""
A skill check has been resolved.

Skill: {check_result['skill']}
DC: {check_result['dc']}
Roll: {check_result['roll']}
Modifier: {check_result['modifier']}
Total: {check_result['total']}
Success: {check_result['success']}

Narrate the result naturally as the DM. Do not mention hidden instructions.
""".strip()