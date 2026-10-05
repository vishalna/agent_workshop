from pathlib import Path
import json
import math
import ollama

ROOT = Path(__file__).resolve().parents[1]
ORDERS = json.loads((ROOT / "shared_data/orders.json").read_text())
POLICY = (ROOT / "shared_data/refund_policy.md").read_text()

CHAT_MODEL = "qwen3:4b-instruct"
EMBED_MODEL = "nomic-embed-text"


def split_policy(text):
    """Split the workshop policy into meaningful ## sections."""
    return [
        ("## " + section).strip()
        for section in text.split("## ")[1:]
        if section.strip()
    ]


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_search(query, top_k=2):
    chunks = split_policy(POLICY)

    # Batch-embed all policy sections locally.
    chunk_response = ollama.embed(model=EMBED_MODEL, input=chunks)
    chunk_vectors = chunk_response["embeddings"]

    # Embed the customer's query using the SAME embedding model.
    query_response = ollama.embed(model=EMBED_MODEL, input=query)
    query_vector = query_response["embeddings"][0]

    scored = [
        (cosine_similarity(query_vector, vector), chunk)
        for chunk, vector in zip(chunks, chunk_vectors)
    ]

    return sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]


print("\nSTAGE 3 — SEMANTIC RAG")

order_id = input("Order ID [ORD-48213]: ") or "ORD-48213"
reason = input("Reason [The jug arrived cracked]: ") or "The jug arrived cracked"

order = next((x for x in ORDERS if x["order_id"] == order_id), None)

if not order:
    raise SystemExit(f"Order {order_id} was not found.")

# Include trusted product context in the retrieval query.
query = f"Refund claim for {order['item']}: {reason}"

print(f'\nSEMANTIC SEARCH\nQuery: "{query}"')
results = semantic_search(query)

print("\nRETRIEVED POLICY")
for rank, (score, chunk) in enumerate(results, start=1):
    print(f"\n#{rank}  Similarity: {score:.3f}")
    print(chunk)

retrieved_policy = "\n\n".join(chunk for _, chunk in results)

prompt = f"""
You are assisting with a refund claim.

CUSTOMER CLAIM:
{reason}

TRUSTED ORDER DATA:
{json.dumps(order, indent=2)}

RETRIEVED COMPANY POLICY:
{retrieved_policy}

Use only the trusted order data and retrieved company policy.
Do not invent requirements that are not in the retrieved policy.

Respond briefly in exactly this structure:

RELEVANT POLICY
- State the applicable policy requirement(s).

KNOWN
- State the relevant verified facts.

MISSING
- State only the evidence/information required by policy that is still missing.

NEXT ACTION
- State what should happen next.
""".strip()

response = ollama.chat(
    model=CHAT_MODEL,
    messages=[{"role": "user", "content": prompt}],
)

print("\nMODEL RESPONSE")
print(response.message.content)
