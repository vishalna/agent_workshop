"""Stage 1: show why an LLM response is not the same as a grounded decision.

The model receives only customer-supplied claims. It has no order database,
refund history, or company policy. The point is to observe how plausible
language can still be unsupported.
"""

import ollama

MODEL = "qwen3:4b-instruct"

print("\nSTAGE 1 — LLM ONLY")
order_id = input("Order ID [ORD-48213]: ") or "ORD-48213"
reason = input("Reason [The jug arrived cracked]: ") or "The jug arrived cracked"
requested = float(input("Requested refund [49]: ") or "49")

prompt = f"""
A customer requests a refund.
Order ID: {order_id}
Reason: {reason}
Requested refund: ${requested:g}

Decide whether the facts are sufficient and state what should happen.
Keep the answer brief.
""".strip()

response = ollama.chat(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
)

print("\nMODEL RESPONSE")
print(response.message.content)
print("\nNOTICE: no real order record or company policy was supplied.")
