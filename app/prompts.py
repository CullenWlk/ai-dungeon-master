from app.config import SYSTEM_PROMPT

def build_prompt(user_input: str) -> str:
    return f"{SYSTEM_PROMPT}\n\nUser: {user_input}\nAssistant:"