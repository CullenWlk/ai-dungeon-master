from app.context.session import load_session_context, format_session_context
from app.character.sheet import load_character_sheet
from app.state.session_state import create_session_state, trim_history
from app.prompts import build_messages, build_json_messages, build_roll_result_prompt
from app.llm_client import generate_response
from app.config import OPENING_PROMPT
from app.adjudication.action_phase import build_action_prompt, parse_action_response
from app.adjudication.pending_phase import build_pending_prompt, parse_pending_response, is_roll_command
from app.mechanics.checks import resolve_skill_check

def chat():
    print("Local AI Chatbot (type 'quit' to exit)\n")

    session_data = load_session_context()
    session_context = format_session_context(session_data)
    character_sheet = load_character_sheet()

    state = create_session_state(session_context)

    opening_messages = build_messages(
        user_input=OPENING_PROMPT,
        session_context=state["session_context"],
        history=[]
    )

    opening_reply = generate_response(opening_messages)
    print("\nAI:")
    print(opening_reply)
    print()

    state["history"].append({"role": "user", "content": OPENING_PROMPT})
    state["history"].append({"role": "assistant", "content": opening_reply})

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "quit":
            break

        if state["pending_check"] is None:
            action_prompt = build_action_prompt(user_input)

            messages = build_json_messages(
                user_input=action_prompt,
                session_context=state["session_context"],
                history=trim_history(state["history"])
            )

            raw_reply = generate_response(messages)
            result = parse_action_response(raw_reply)

            if result["action_type"] == "narration":
                print("\nAI:")
                print(result["display_text"])
                print()

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": result["display_text"]})

            elif result["action_type"] == "request_check":
                print("\nAI:")
                print(result["display_text"])
                print()

                state["pending_check"] = {
                    "roll_type": result["roll_type"],
                    "skill": result["skill"],
                    "dc": result["dc"],
                    "reason": result["reason"]
                }

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": result["display_text"]})

        else:
            if is_roll_command(user_input):
                check_result = resolve_skill_check(
                    character_sheet,
                    state["pending_check"]["skill"],
                    state["pending_check"]["dc"]
                )

                narration_prompt = build_roll_result_prompt(check_result)

                messages = build_messages(
                    user_input=narration_prompt,
                    session_context=state["session_context"],
                    history=trim_history(state["history"])
                )

                reply = generate_response(messages)

                print("\nAI:")
                print(reply)
                print()

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": reply})

                state["pending_check"] = None

            else:
                pending_prompt = build_pending_prompt(user_input, state["pending_check"])

                messages = build_json_messages(
                    user_input=pending_prompt,
                    session_context=state["session_context"],
                    history=trim_history(state["history"])
                )

                raw_reply = generate_response(messages)
                result = parse_pending_response(raw_reply)

                print("\nAI:")
                print(result["display_text"])
                print()

                if result["action_type"] == "modify_check":
                    state["pending_check"]["skill"] = result["skill"]
                    state["pending_check"]["dc"] = result["dc"]

                elif result["action_type"] == "change_approach":
                    state["pending_check"] = None

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": result["display_text"]})

if __name__ == "__main__":
    chat()