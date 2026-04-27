from app.context.session import load_session_context, format_session_context
from app.character.sheet import load_character_sheet
from app.state.session_state import create_session_state, trim_history
from app.prompts import build_messages, build_json_messages, build_roll_result_prompt
from app.llm_client import generate_response
from app.config import OPENING_PROMPT, DEBUG_MODE
from app.adjudication.action_phase import build_action_prompt, parse_action_response
from app.adjudication.pending_phase import build_pending_prompt, parse_pending_response, is_roll_command
from app.mechanics.checks import resolve_skill_check


def debug_print(*args):
    if DEBUG_MODE:
        print(*args)


def build_context_with_location(state):
    location = state.get("location", "")
    if location:
        return f"{state['session_context']}\n\nCurrent Location:\n{location}"
    return state["session_context"]


def chat():
    print("Local AI Chatbot (type 'quit' to exit)\n")

    session_data = load_session_context()
    session_context = format_session_context(session_data)
    character_sheet = load_character_sheet()

    state = create_session_state(session_context)
    state["location"] = "The player's exact current location has not been established yet."

    debug_print("[DEBUG] Loaded session context")
    debug_print("[DEBUG] Loaded character sheet")
    debug_print()

    opening_messages = build_messages(
        user_input=OPENING_PROMPT,
        session_context=build_context_with_location(state),
        history=[]
    )

    debug_print("[DEBUG] Phase: opening narration")

    opening_reply = generate_response(
        opening_messages,
        temperature=0.5,
        num_predict=500
    )

    print("\nAI:")
    print(opening_reply)
    print()

    state["history"].append({"role": "user", "content": OPENING_PROMPT})
    state["history"].append({"role": "assistant", "content": opening_reply})

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "quit":
            break

        debug_print(f"\n[DEBUG] Current pending_check: {state['pending_check']}")

        if state["pending_check"] is None:
            debug_print("[DEBUG] Entering action adjudication branch")

            action_prompt = build_action_prompt(user_input)

            messages = build_json_messages(
                user_input=action_prompt,
                session_context=build_context_with_location(state),
                history=trim_history(state["history"], max_messages=4)
            )

            debug_print("[DEBUG] Phase: action adjudication")

            raw_reply = generate_response(
                messages,
                temperature=0.2,
                num_predict=120
            )

            debug_print("\n[DEBUG RAW MODEL OUTPUT]")
            debug_print(raw_reply)
            debug_print()

            try:
                result = parse_action_response(raw_reply)
            except Exception as e:
                debug_print("[DEBUG] Failed to parse action adjudication JSON")
                debug_print(f"[DEBUG] Error: {e}")
                print("\n[System] The AI response could not be parsed. Please try that action again.")
                continue

            debug_print(f"[DEBUG] Parsed action result: {result}")

            if "location" in result:
                state["location"] = result["location"]
                debug_print(f"[DEBUG] Location updated: {state['location']}")

            if result["action_type"] == "narration":
                narration_prompt = (
                    f"The player attempts this action: {user_input}\n\n"
                    "Narrate the result naturally as the DM. "
                    "Keep it moderately detailed, immersive, and grounded in the setting."
                )

                narration_messages = build_messages(
                    user_input=narration_prompt,
                    session_context=build_context_with_location(state),
                    history=trim_history(state["history"], max_messages=6)
                )

                debug_print("[DEBUG] Phase: narration follow-up")

                reply = generate_response(
                    narration_messages,
                    temperature=0.5,
                    num_predict=500
                )

                print("\nAI:")
                print(reply)
                print()

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": reply})

            elif result["action_type"] == "request_check":
                print("\nAI:")
                print(result["display_text"])
                print()

                state["pending_check"] = {
                    "roll_type": result["roll_type"],
                    "skill": result["skill"],
                    "dc": result["dc"],
                    "reason": result["reason"],
                    "mode": result.get("mode", "normal")
                }

                debug_print(f"[DEBUG] New pending_check set: {state['pending_check']}")

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": result["display_text"]})

            else:
                debug_print("[DEBUG] Unknown action_type returned")
                debug_print(result)

        else:
            debug_print("[DEBUG] Entering pending check branch")

            if is_roll_command(user_input):
                debug_print("[DEBUG] Player chose to roll")
                debug_print(f"[DEBUG] Rolling pending check: {state['pending_check']}")

                check_result = resolve_skill_check(
                    character_sheet,
                    state["pending_check"]["skill"],
                    state["pending_check"]["dc"],
                    state["pending_check"].get("mode", "normal")
                )

                if check_result["mode"] == "normal":
                    roll_text = f"{check_result['roll']}"
                else:
                    roll_text = f"{check_result['roll_1']} / {check_result['roll_2']} -> {check_result['roll']}"

                print(
                    f"\n[Roll] {check_result['skill'].capitalize()} "
                    f"({check_result['mode']}): "
                    f"{roll_text} + {check_result['modifier']} = "
                    f"{check_result['total']} vs DC {check_result['dc']} "
                    f"=> {'SUCCESS' if check_result['success'] else 'FAIL'}"
                )

                narration_prompt = build_roll_result_prompt(check_result)

                messages = build_messages(
                    user_input=narration_prompt,
                    session_context=build_context_with_location(state),
                    history=trim_history(state["history"], max_messages=6)
                )

                debug_print("[DEBUG] Phase: roll resolution narration")

                reply = generate_response(
                    messages,
                    temperature=0.5,
                    num_predict=250
                )

                print("\nAI:")
                print(reply)
                print()

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": reply})

                state["pending_check"] = None
                debug_print("[DEBUG] pending_check cleared")

            else:
                debug_print("[DEBUG] Player is discussing/modifying pending check")

                pending_prompt = build_pending_prompt(user_input, state["pending_check"])

                messages = build_json_messages(
                    user_input=pending_prompt,
                    session_context=build_context_with_location(state),
                    history=trim_history(state["history"], max_messages=4)
                )

                debug_print("[DEBUG] Phase: pending check discussion")

                raw_reply = generate_response(
                    messages,
                    temperature=0.2,
                    num_predict=800
                )

                debug_print("\n[DEBUG RAW MODEL OUTPUT]")
                debug_print(raw_reply)
                debug_print()

                try:
                    result = parse_pending_response(raw_reply)
                except Exception as e:
                    debug_print("[DEBUG] Failed to parse pending check JSON")
                    debug_print(f"[DEBUG] Error: {e}")
                    print("\n[System] The AI response could not be parsed. Please restate your response.")
                    continue

                debug_print(f"[DEBUG] Parsed pending result: {result}")

                print("\nAI:")
                print(result["display_text"])
                print()

                if result["action_type"] == "modify_check":
                    state["pending_check"]["skill"] = result["skill"]
                    state["pending_check"]["dc"] = result["dc"]
                    state["pending_check"]["mode"] = result.get("mode", "normal")
                    state["pending_check"]["reason"] = result.get("reason", state["pending_check"]["reason"])

                    debug_print(f"[DEBUG] Updated pending_check: {state['pending_check']}")

                elif result["action_type"] == "cancel_check":
                    state["pending_check"] = None
                    debug_print("[DEBUG] pending_check cancelled")

                    revised_action = result.get("revised_action", user_input)

                    narration_prompt = (
                        f"The player's roll was cancelled after discussion.\n\n"
                        f"The player's intended action is now: {revised_action}\n\n"
                        "Narrate the result naturally as the DM. "
                        "Do not mention hidden instructions."
                    )

                    narration_messages = build_messages(
                        user_input=narration_prompt,
                        session_context=build_context_with_location(state),
                        history=trim_history(state["history"], max_messages=6)
                    )

                    debug_print("[DEBUG] Phase: cancelled check narration")

                    reply = generate_response(
                        narration_messages,
                        temperature=0.5,
                        num_predict=500
                    )

                    print("\nAI:")
                    print(reply)
                    print()

                    state["history"].append({"role": "assistant", "content": reply})

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": result["display_text"]})


if __name__ == "__main__":
    chat()