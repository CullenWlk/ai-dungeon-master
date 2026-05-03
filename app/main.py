import json
import tiktoken

from app.context.session import load_session_context, format_session_context
from app.character.sheet import load_character_sheet
from app.state.session_state import create_session_state, trim_history
from app.prompts import build_messages, build_json_messages, build_roll_result_prompt
from app.llm_client import generate_response
from app.config import OPENING_PROMPT, DEBUG_MODE
from app.adjudication.action_phase import build_action_prompt, parse_action_response
from app.adjudication.pending_phase import build_pending_prompt, parse_pending_response, is_roll_command
from app.mechanics.checks import resolve_skill_check

try:
    from app.config import RAG_ENABLED
    from app.rag.retriever import retrieve_lore, format_lore_context
except ImportError:
    RAG_ENABLED = False
    retrieve_lore = None
    format_lore_context = None


def debug_print(*args):
    if DEBUG_MODE:
        print(*args, flush=True)

def count_tokens(text):
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4  # fallback rough estimate

def format_session_memory(state):
    memory = state.get("session_memory", {})

    if not memory:
        return ""

    lines = ["Temporary Session Memory:"]

    for key, value in memory.items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def build_context_with_location(state):
    location = state.get("location", "")
    interaction_context = state.get("interaction_context", "")
    story_summary = state.get("story_summary", "")

    context = state["session_context"]

    if location:
        context += f"\n\nCurrent Location:\n{location}"

    if interaction_context:
        context += f"\n\nCurrent Interaction:\n{interaction_context}"

    if story_summary:
        context += f"\n\nStory Summary So Far:\n{story_summary}"

    session_memory = format_session_memory(state)
    if session_memory:
        context += f"\n\n{session_memory}"

    return context


def build_context_with_location_and_lore(state, user_input=None):
    context = build_context_with_location(state)

    if not RAG_ENABLED or not user_input or retrieve_lore is None:
        return context

    query = f"{state.get('location', '')}\n{user_input}"

    try:
        lore_entries = retrieve_lore(query)

        debug_print(f"[DEBUG] RAG retrieved {len(lore_entries)} entries:")

        for i, entry in enumerate(lore_entries):
            preview = entry["text"].split("\n")[0][:60]
            debug_print(f"[DEBUG] {i+1}. ({entry['source']}) {preview}...")

        lore_context = format_lore_context(lore_entries)

        if lore_context:
            context += f"\n\nRelevant Lore:\n{lore_context}"
            debug_print("[DEBUG] RAG lore injected into context")

    except Exception as e:
        debug_print("[DEBUG] RAG retrieval failed")
        debug_print(f"[DEBUG] Error: {e}")

    return context


def update_story_summary(state, user_input, ai_reply):
    summary_prompt = (
        "You are maintaining a compact running summary for an ongoing fantasy RPG session.\n\n"
        "Rewrite the entire story summary from scratch using the existing summary and the latest turn.\n"
        "Do NOT append new sentences onto the old summary.\n"
        "Blend the newest important events into the older summary.\n"
        "Compress older events into shorter wording as the story grows.\n"
        "Preserve only important facts: major actions, goals, locations, NPCs, consequences, discoveries, conflicts, and unresolved threads.\n"
        "Remove minor moment-to-moment description, repeated atmosphere, and details that no longer matter.\n\n"
        f"Existing summary:\n{state.get('story_summary', 'No major events have happened yet.')}\n\n"
        f"Latest player action:\n{user_input}\n\n"
        f"Latest DM response:\n{ai_reply}\n\n"
        "Return only the new complete story summary.\n"
        "The summary must cover the whole story so far, including the latest turn.\n"
        "The summary must be under 7 sentences.\n"
        "Do not use bullet points.\n"
        "Do not include labels like 'Summary:' or explanations."
    )

    messages = build_messages(
        user_input=summary_prompt,
        session_context=build_context_with_location(state),
        history=[]
    )

    new_summary = generate_response(
        messages,
        temperature=0.2,
        num_predict=500,
        think=False
    )

    state["story_summary"] = new_summary.strip()
    debug_print(f"[DEBUG] Story summary updated: {state['story_summary']}")


def update_session_memory_from_turn(state, user_input, ai_reply):
    memory_prompt = (
        "You are updating temporary session memory for an ongoing fantasy RPG.\n\n"
        "Session memory stores important changes connected to specific people, NPCs, locations, factions, objects, or lore entries.\n"
        "This memory is temporary for the current session only.\n\n"
        "For NPCs and named people, prioritize relationship changes with the player. Track whether the NPC is friendly, hostile, suspicious, loyal, afraid, attracted, romantically involved, married to the player, employed by the player, commanded by the player, allied, rival, enemy, mentor, student, boss, subordinate, or otherwise socially connected to the player.\n"
        "Also track important changes to that NPC's circumstances, promises, injuries, secrets, debts, trust, grudges, obligations, or knowledge about the player.\n\n"
        "For locations, factions, objects, and other lore entries, track only important changes caused by play, such as damage, ownership, reputation, access, danger, control, discovered secrets, or changed attitudes toward the player.\n\n"
        "Do not record generic atmosphere, minor movement, repeated descriptions, or unimportant details.\n"
        "Do not record static lore unless something changed during play.\n\n"
        f"Current session memory:\n{json.dumps(state.get('session_memory', {}), indent=2)}\n\n"
        f"Latest player action:\n{user_input}\n\n"
        f"Latest DM response:\n{ai_reply}\n\n"
        "Return JSON only in this format:\n"
        "{\n"
        '  "updates": [\n'
        '    {\n'
        '      "key": "Specific NPC, location, faction, object, or lore entry name",\n'
        '      "value": "One concise sentence describing the full updated temporary memory for that key."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- If nothing important changed, return {\"updates\": []}.\n"
        "- Do not make entries for unnamed or unimportant characters the player has only done something small like ask a question to."
        "- Do not make entries for locations unless the player has changed something at that location. For example, do not make a entry about a tavern because the player sat at one of the back tables, he did not change anything about the tavern so you should not make an entry about it."
        "- Use specific keys like an NPC name, tavern name, city district, faction, or item.\n"
        "- For NPCs, include their current relationship to the player if relevant.\n"
        "- If an entry already exists, rewrite the value as the full updated memory for that key, not just the new detail.\n"
        "- Each value should be one concise sentence.\n"
        "- Return valid JSON only.\n"
        "- Do not wrap JSON in markdown."
    )

    messages = build_json_messages(
        user_input=memory_prompt,
        session_context=build_context_with_location(state),
        history=[]
    )

    raw_reply = generate_response(
        messages,
        temperature=0.1,
        num_predict=350,
        think=False
    )

    debug_print("\n[DEBUG SESSION MEMORY RAW OUTPUT]")
    debug_print(raw_reply)
    debug_print()

    try:
        result = json.loads(raw_reply)
    except Exception as e:
        debug_print("[DEBUG] Failed to parse session memory JSON")
        debug_print(f"[DEBUG] Error: {e}")
        return

    updates = result.get("updates", [])

    if not updates:
        debug_print("[DEBUG] No session memory updates")
        return

    state.setdefault("session_memory", {})

    for update in updates:
        key = update.get("key", "").strip()
        value = update.get("value", "").strip()

        if key and value:
            state["session_memory"][key] = value
            debug_print(f"[DEBUG] Session memory updated: {key} -> {value}")


def update_memory_systems(state, user_input, ai_reply):
    update_story_summary(state, user_input, ai_reply)
    update_session_memory_from_turn(state, user_input, ai_reply)


def chat():
    print("Your AI DM (type 'quit' to exit)\n", flush=True)

    session_data = load_session_context()
    session_context = format_session_context(session_data)
    character_sheet = load_character_sheet()

    state = create_session_state(session_context)
    state["location"] = "The player's exact current location has not been established yet."
    state["story_summary"] = "No major events have happened yet."
    state["session_memory"] = {}

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
        r_pen=1.5,
        num_predict=5000
    )

    print(opening_reply, flush=True)
    print(flush=True)

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
                num_predict=250,
                think=False
            )

            debug_print("\n[DEBUG RAW MODEL OUTPUT]")
            debug_print(raw_reply)
            debug_print()

            try:
                result = parse_action_response(raw_reply)
            except Exception as e:
                debug_print("[DEBUG] Failed to parse action adjudication JSON")
                debug_print(f"[DEBUG] Error: {e}")
                print("\n[System] The AI response could not be parsed. Please try that action again.", flush=True)
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
                    session_context=build_context_with_location_and_lore(state, user_input),
                    history=trim_history(state["history"], max_messages=6)
                )

                debug_print("[DEBUG] Phase: narration follow-up")

                if DEBUG_MODE:
                    system_tokens = count_tokens(state["session_context"])
                    summary_tokens = count_tokens(state.get("story_summary", ""))
                    memory_tokens = count_tokens(format_session_memory(state))
                    history_tokens = count_tokens(str(messages))
    
                    debug_print(f"\n[DEBUG] TOKENS:")
                    debug_print(f"  session_context: {system_tokens}")
                    debug_print(f"  story_summary: {summary_tokens}")
                    debug_print(f"  session_memory: {memory_tokens}")
                    debug_print(f"  history tokens: {history_tokens}")
                    debug_print(f"  total_estimate: {system_tokens + summary_tokens + memory_tokens + history_tokens}")

                reply = generate_response(
                    narration_messages,
                    temperature=0.5,
                    r_pen=1.5,
                    num_predict=5000
                )

                print("\n", flush=True)
                print(reply, flush=True)
                print(flush=True)

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": reply})
                update_memory_systems(state, user_input, reply)

            elif result["action_type"] == "request_check":
                print("\n", flush=True)
                print(result["display_text"], flush=True)
                print(flush=True)

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
                    f"=> {'SUCCESS' if check_result['success'] else 'FAIL'}",
                    flush=True
                )

                narration_prompt = build_roll_result_prompt(check_result)

                messages = build_messages(
                    user_input=narration_prompt,
                    session_context=build_context_with_location_and_lore(state, user_input),
                    history=trim_history(state["history"], max_messages=6)
                )

                debug_print("[DEBUG] Phase: roll resolution narration")

                reply = generate_response(
                    messages,
                    temperature=0.5,
                    r_pen=1.5,
                    num_predict=5000
                )

                print("\n", flush=True)
                print(reply, flush=True)
                print(flush=True)

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": reply})
                update_memory_systems(state, user_input, reply)

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
                    r_pen=1.5,
                    num_predict=5000
                )

                debug_print("\n[DEBUG RAW MODEL OUTPUT]")
                debug_print(raw_reply)
                debug_print()

                try:
                    result = parse_pending_response(raw_reply)
                except Exception as e:
                    debug_print("[DEBUG] Failed to parse pending check JSON")
                    debug_print(f"[DEBUG] Error: {e}")
                    print("\n[System] The AI response could not be parsed. Please restate your response.", flush=True)
                    continue

                debug_print(f"[DEBUG] Parsed pending result: {result}")

                print("\nDM:", flush=True)
                print(result["display_text"], flush=True)
                print(flush=True)

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
                        session_context=build_context_with_location_and_lore(state, revised_action),
                        history=trim_history(state["history"], max_messages=6)
                    )

                    debug_print("[DEBUG] Phase: cancelled check narration")
                    print("[CHECK_CANCELLED]", flush=True)

                    if DEBUG_MODE:
                        system_tokens = count_tokens(state["session_context"])
                        summary_tokens = count_tokens(state.get("story_summary", ""))
                        memory_tokens = count_tokens(format_session_memory(state))
                        history_tokens = count_tokens(str(messages))
    
                        debug_print(f"\n[DEBUG] TOKENS:")
                        debug_print(f"  session_context: {system_tokens}")
                        debug_print(f"  story_summary: {summary_tokens}")
                        debug_print(f"  session_memory: {memory_tokens}")
                        debug_print(f"  history tokens: {history_tokens}")
                        debug_print(f"  total_estimate: {system_tokens + summary_tokens + memory_tokens + history_tokens}")

                    reply = generate_response(
                        narration_messages,
                        temperature=0.5,
                        r_pen=1.5,
                        num_predict=5000
                    )

                    print(reply, flush=True)
                    print(flush=True)

                    state["history"].append({"role": "assistant", "content": reply})
                    update_memory_systems(state, revised_action, reply)

                state["history"].append({"role": "user", "content": user_input})
                state["history"].append({"role": "assistant", "content": result["display_text"]})


if __name__ == "__main__":
    chat()