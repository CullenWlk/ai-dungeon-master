def create_session_state(session_context):
    return {
        "session_context": session_context,
        "history": [],
        "pending_check": None
    }

def trim_history(history, max_messages=10):
    return history[-max_messages:]