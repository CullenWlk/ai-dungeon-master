from pathlib import Path

import chromadb
import ollama

from app.config import CHROMA_DIR, LOREBOOK_DIR, LORE_COLLECTION_NAME, EMBED_MODEL


def embed_text(text):
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )
    return response["embedding"]


def load_lore_entries():
    lore_dir = Path(LOREBOOK_DIR)
    entries = []

    for path in lore_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        chunks = [chunk.strip() for chunk in text.split("---") if chunk.strip()]

        for index, chunk in enumerate(chunks):
            entries.append({
                "id": f"{path.stem}_{index}",
                "text": chunk,
                "source": path.name
            })

    return entries


def reset_collection(client):
    try:
        client.delete_collection(name=LORE_COLLECTION_NAME)
        print(f"Cleared existing collection: {LORE_COLLECTION_NAME}")
    except Exception:
        print(f"No existing collection to clear: {LORE_COLLECTION_NAME}")

    return client.get_or_create_collection(name=LORE_COLLECTION_NAME)


def ingest_lore():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = reset_collection(client)

    entries = load_lore_entries()

    if not entries:
        print("No lore entries found.")
        return

    ids = []
    documents = []
    metadatas = []
    embeddings = []

    for entry in entries:
        ids.append(entry["id"])
        documents.append(entry["text"])
        metadatas.append({"source": entry["source"]})
        embeddings.append(embed_text(entry["text"]))

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    print(f"Ingested {len(entries)} lore entries.")


if __name__ == "__main__":
    ingest_lore()