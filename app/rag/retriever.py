import chromadb
import ollama

from app.config import CHROMA_DIR, LORE_COLLECTION_NAME, EMBED_MODEL, RAG_MAX_RESULTS


def embed_query(text):
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )
    return response["embedding"]


def retrieve_lore(query, max_results=RAG_MAX_RESULTS):
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name=LORE_COLLECTION_NAME)

    query_embedding = embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=max_results
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    entries = []

    for doc, meta in zip(documents, metadatas):
        entries.append({
            "text": doc,
            "source": meta.get("source", "unknown")
        })

    return entries


def format_lore_context(entries):
    if not entries:
        return ""

    blocks = []
    for entry in entries:
        blocks.append(f"Source: {entry['source']}\n{entry['text']}")

    return "\n\n".join(blocks)