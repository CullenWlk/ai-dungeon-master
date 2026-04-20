import ollama

MODEL_NAME = "qwen3.5:4b"

def chat():
    print("Local AI Chatbot (type 'quit' to exit)\n")

    while True:
        user_input = input("> ")

        if user_input.lower() == "quit":
            break

        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful fantasy RPG assistant."},
                {"role": "user", "content": user_input}
            ]
        )

        print(response["message"]["content"])

if __name__ == "__main__":
    chat()