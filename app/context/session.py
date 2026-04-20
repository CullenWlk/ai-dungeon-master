import json

def load_session_context(path="app/data/session_context.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def format_session_context(data):
    return (
        f"Character:\n{data['character']}\n\n"
        f"Setting:\n{data['setting']}\n\n"
        f"Story Premise:\n{data['story_prompt']}"
    )