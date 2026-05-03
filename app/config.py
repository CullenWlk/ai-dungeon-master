MODEL_NAME = "deepseek-r1:8b"
TEMPERATURE = 0.7

OPENING_PROMPT = (
    "Begin the story. Write the opening narration for the scene using the character, "
    "setting, and story premise provided. Establish the immediate atmosphere and situation. Keep it to one short paragraph, or two brief paragraphs at most."
)

DEBUG_MODE = True
CHROMA_DIR = "app/data/chroma_db"
LOREBOOK_DIR = "app/data/lorebook"
LORE_COLLECTION_NAME = "lorebook"
EMBED_MODEL = "embeddinggemma"
RAG_MAX_RESULTS = 3
RAG_ENABLED = True