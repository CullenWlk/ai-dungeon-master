import ollama
from app.config import MODEL_NAME, TEMPERATURE

def generate_response(messages, temperature=None, num_predict=None, think=False):
    temp = TEMPERATURE if temperature is None else temperature

    options = {
        "temperature": temp
    }

    if num_predict is not None:
        options["num_predict"] = num_predict

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        think=think,
        options=options
    )

    return response["message"]["content"]