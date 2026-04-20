import ollama
from app.config import MODEL_NAME, TEMPERATURE

def generate_response(prompt: str) -> str:
    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        options={
            "temperature": TEMPERATURE
        }
    )
    return response["response"]