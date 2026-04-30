import json
from pathlib import Path


def load_session_context(path=None):
    if path is not None:
        context_path = Path(path)
    else:
        session_path = Path("app/data/current_session_context.json")
        default_path = Path("app/data/session_context.json")
        context_path = session_path if session_path.exists() else default_path

    with open(context_path, "r", encoding="utf-8") as file:
        return json.load(file)


def format_session_context(data):
    return (
        f"Character:\n{data['character']}\n\n"
        f"Setting:\n{data['setting']}\n\n"
        f"Story Premise:\n{data['story_prompt']}"
    )