"""Stage 2: add trusted system-of-record data.

Python performs explicit lookups. The LLM does not choose tools yet. This
separates trusted facts from the customer's unverified claim.
"""

from pathlib import Path
import json
import ollama

ROOT = Path(__file__).resolve().parents[1]
MODEL = "qwen3:4b-instruct"

ORDERS = json.loads((ROOT / "shared_data/orders.json").read_text())
HISTORY = json.loads((ROOT / "shared_data/refund_history.json").read_text())


def get_order(order_id):
    """Simulate an OMS lookup."""
    return next((row for row in ORDERS if row["order_id"] == order_id), None)


def get_refund_history(customer_id):
    """Simulate a CRM/risk-history lookup."""
    return HISTORY.get(customer_id, {"refunds_last_12m": 0})


print("\nSTAGE 2 — TRUSTED TOOLS")
order_id = input("Order ID [ORD-48213]: ") or "ORD-48213"
reason = input("Reason [The jug arrived cracked]: ") or "The jug arrived cracked"

order = get_order(order_id)
if not order:
    raise SystemExit(f"Order {order_id} was not found.")

refund_history = get_refund_history(order["customer_id"])

print("\nTOOL → get_order")
print(json.dumps(order, indent=2))
print("\nTOOL → get_refund_history")
print(json.dumps(refund_history, indent=2))

prompt = f"""
CUSTOMER CLAIM:
{reason}

TRUSTED ORDER:
{json.dumps(order, indent=2)}

TRUSTED REFUND HISTORY:
{json.dumps(refund_history, indent=2)}

Explain briefly:
1. what is verified,
2. what remains unverified,
3. whether company refund policy is available.

Do not invent policy requirements.
""".strip()

response = ollama.chat(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
)

print("\nMODEL RESPONSE")
print(response.message.content)
