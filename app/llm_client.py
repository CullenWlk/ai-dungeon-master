import ollama
from app.config import MODEL_NAME, TEMPERATURE, DEBUG_MODE

def generate_response(messages, temperature=None, r_pen=1.0, num_predict=None, think=True):
    temp = TEMPERATURE if temperature is None else temperature

    options = {
        "temperature": temp,
        "top_p": 0.95,
        "top_k": 20,
        "repeat_penalty": 1.1,
        "presence_penalty": 1.5,
    }

    if num_predict is not None:
        options["num_predict"] = num_predict

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        think=think,
        options=options
    )

    message = response.get("message", {})

    thinking = message.get("thinking", "")

    if DEBUG_MODE and think:
        print("\n[THINKING]")
        print(thinking)
        print("[END THINKING]\n", flush=True)

    return response["message"]["content"]