import ollama
from app.config import MODEL_NAME, TEMPERATURE

def generate_response(messages, temperature=None):
    temp = temperature if temperature is not None else TEMPERATURE

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={
            "temperature": temp
        }
    )
    return response["message"]["content"]