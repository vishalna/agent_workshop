from pathlib import Path
import json
import ollama

ROOT = Path(__file__).resolve().parents[1]
ORDERS = json.loads((ROOT / "shared_data/orders.json").read_text())
HISTORY = json.loads((ROOT / "shared_data/refund_history.json").read_text())

MODEL = "qwen3:4b-instruct"


def classify_claim(reason):
    """LLM does semantic interpretation only; it does NOT make the refund decision."""
    prompt = f"""
Classify this refund reason into exactly one category:

DAMAGED_ITEM
MISSING_PARCEL
WRONG_ITEM
OTHER

Refund reason: {reason}

Return only the category name. No explanation.
""".strip()

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    category = response.message.content.strip().upper()

    allowed = {"DAMAGED_ITEM", "MISSING_PARCEL", "WRONG_ITEM", "OTHER"}
    return category if category in allowed else "OTHER"


def apply_guardrails(order, history, claim_type, requested_refund, photo_supplied):
    """Hard business controls live in deterministic Python code."""

    if order is None:
        return "HUMAN_REVIEW", "Order could not be verified"

    amount_paid = float(order["amount_paid"])

    if requested_refund > amount_paid:
        return "BLOCKED", "Requested refund exceeds amount paid"

    if requested_refund > 200:
        return "HUMAN_REVIEW", "Requested refund exceeds $200 hard automation cap"

    if requested_refund > 75:
        return "HUMAN_REVIEW", "Requested refund exceeds $75 auto-approval threshold"

    if claim_type == "DAMAGED_ITEM" and not photo_supplied:
        return "NEEDS_INFORMATION", "Photo evidence is required for a damaged-item claim"

    refunds_last_12m = int(history.get("refunds_last_12m", 0)) if history else 0
    if refunds_last_12m >= 3:
        return "HUMAN_REVIEW", "Customer has 3 or more refunds in the last 12 months"

    return "AUTO_APPROVE", "All deterministic controls passed"


print("\nSTAGE 4 — LLM CLASSIFICATION + DETERMINISTIC GUARDRAILS")

order_id = input("Order ID [ORD-48213]: ") or "ORD-48213"
reason = input("Reason [The jug arrived cracked]: ") or "The jug arrived cracked"
requested = float(input("Requested refund [49]: ") or "49")
photo_text = (input("Photo supplied? [no]: ") or "no").strip().lower()
photo_supplied = photo_text in {"y", "yes", "true", "1"}

order = next((x for x in ORDERS if x["order_id"] == order_id), None)

history = None
if order:
    # HISTORY is keyed by customer_id, so bind directly to the trusted ID.
    history = HISTORY.get(
        order["customer_id"],
        {"refunds_last_12m": 0},
    )

print("\nLLM INTERPRETATION")
claim_type = classify_claim(reason)
print(f"Customer text : {reason}")
print(f"Claim type    : {claim_type}")

print("\nDETERMINISTIC INPUTS")
print(f"Amount paid       : ${order['amount_paid'] if order else 'UNKNOWN'}")
print(f"Requested refund  : ${requested:g}")
print(f"Photo supplied    : {photo_supplied}")
print(f"Refunds last 12m  : {history.get('refunds_last_12m', 'UNKNOWN') if history else 'UNKNOWN'}")

decision, why = apply_guardrails(
    order=order,
    history=history,
    claim_type=claim_type,
    requested_refund=requested,
    photo_supplied=photo_supplied,
)

print("\nGUARDRAIL DECISION")
print(f"DECISION: {decision}")
print(f"WHY: {why}")

print("\nTEACHING POINT")
print("The LLM interpreted natural language; deterministic code made the business decision.")
