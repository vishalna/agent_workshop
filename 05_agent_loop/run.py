from pathlib import Path
import json
import ollama

ROOT = Path(__file__).resolve().parents[1]
ORDERS = json.loads((ROOT / "shared_data/orders.json").read_text())
HISTORY = json.loads((ROOT / "shared_data/refund_history.json").read_text())
POLICY = (ROOT / "shared_data/refund_policy.md").read_text()

MODEL = "qwen3:4b-instruct"
MAX_STEPS = 8

# Runtime state owned by the orchestrator, not by the LLM.
STATE = {
    "trusted_order": None,
    "policy_searched": False,
    "history_checked": False,
    "proposal_result": None,
    "claim_reason": "",
    "photo_supplied": False,
}


def get_order(order_id: str):
    """Get trusted order data for an order ID."""
    order = next((x for x in ORDERS if x["order_id"] == order_id), None)
    if order:
        STATE["trusted_order"] = order
        return order
    return {"error": "order_not_found"}


def get_refund_history(customer_id: str):
    """Get refund history for a customer ID."""
    # SECURITY / INTEGRITY CONTROL:
    # Never trust an LLM-supplied customer ID if we already know the ID
    # from the authoritative order record.
    trusted = STATE["trusted_order"]
    if trusted:
        trusted_id = trusted["customer_id"]
        if customer_id != trusted_id:
            print("\n⚠ ORCHESTRATOR GUARDRAIL")
            print(f"Model supplied customer_id : {customer_id}")
            print(f"Trusted customer_id        : {trusted_id}")
            print("Rejected model-supplied identifier; binding tool call to trusted ID.")
        customer_id = trusted_id

    result = HISTORY.get(customer_id, {"refunds_last_12m": 0})
    STATE["history_checked"] = True
    return {"customer_id": customer_id, **result}


def _policy_chunks():
    return [
        ("## " + section).strip()
        for section in POLICY.split("## ")[1:]
        if section.strip()
    ]


def search_policy(query: str):
    """Search refund policy for relevant rules."""
    # Keep Stage 5 self-contained and transparent. Stage 3 already teaches
    # embedding retrieval; here the focus is agent orchestration.
    terms = {w.strip(".,:;!?()[]").lower() for w in query.split() if len(w) > 2}
    scored = []
    for chunk in _policy_chunks():
        text = chunk.lower()
        score = sum(1 for term in terms if term in text)
        # Small semantic aliases prevent the old cracked/damaged failure.
        if any(x in query.lower() for x in ("crack", "broken", "damage", "defect")) and "damaged item" in text:
            score += 5
        if any(x in query.lower() for x in ("missing", "lost", "not arrived")) and "missing parcel" in text:
            score += 5
        if any(x in query.lower() for x in ("wrong", "incorrect")) and "wrong item" in text:
            score += 5
        scored.append((score, chunk))

    STATE["policy_searched"] = True
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:2]
    return "\n\n".join(chunk for _, chunk in top)


def check_carrier_scan(order_id: str):
    """Get the trusted carrier status for an order."""
    order = next((x for x in ORDERS if x["order_id"] == order_id), None)

    reason = STATE["claim_reason"].lower()
    missing_case = any(x in reason for x in ("missing", "lost", "not arrived", "never arrived"))
    if not missing_case:
        print("\nℹ ORCHESTRATION NOTE")
        print("Carrier lookup is not required for this damaged-item claim.")
        print("Allowing read-only call for teaching purposes; production could block it to save cost/latency.")

    if not order:
        return {"error": "order_not_found"}
    return {"order_id": order_id, "carrier_status": order["carrier_status"]}


def propose_refund(
    order_id: str,
    requested_amount: float,
    reason: str,
    photo_supplied: bool = False,
):
    """Run the controlled refund proposal through deterministic guardrails."""
    order = STATE["trusted_order"]

    if not order or order["order_id"] != order_id:
        result = {"decision": "HUMAN_REVIEW", "reason": "Order not verified"}
        STATE["proposal_result"] = result
        return result

    if not STATE["policy_searched"]:
        result = {"decision": "HUMAN_REVIEW", "reason": "Policy was not checked"}
        STATE["proposal_result"] = result
        return result

    if not STATE["history_checked"]:
        result = {"decision": "HUMAN_REVIEW", "reason": "Refund history was not checked"}
        STATE["proposal_result"] = result
        return result

    amount_paid = float(order["amount_paid"])
    requested_amount = float(requested_amount)

    if requested_amount > amount_paid:
        result = {"decision": "BLOCKED", "reason": "Requested refund exceeds amount paid"}
    elif requested_amount > 200:
        result = {"decision": "HUMAN_REVIEW", "reason": "Requested refund exceeds $200 automation cap"}
    elif requested_amount > 75:
        result = {"decision": "HUMAN_REVIEW", "reason": "Requested refund exceeds $75 auto-approval threshold"}
    elif any(x in reason.lower() for x in ("crack", "broken", "damage", "defect")) and not photo_supplied:
        result = {"decision": "NEEDS_INFORMATION", "reason": "Photo evidence is required for damaged item"}
    else:
        refunds = HISTORY.get(order["customer_id"], {}).get("refunds_last_12m", 0)
        if refunds >= 3:
            result = {"decision": "HUMAN_REVIEW", "reason": "Repeated refund history"}
        else:
            result = {
                "decision": "AUTO_APPROVE",
                "reason": "All deterministic controls passed",
                "approved_amount": requested_amount,
                "simulation_only": True,
            }

    STATE["proposal_result"] = result
    return result


TOOLS = [
    get_order,
    get_refund_history,
    search_policy,
    check_carrier_scan,
    propose_refund,
]

TOOL_MAP = {fn.__name__: fn for fn in TOOLS}


def execute_tool(name, args):
    fn = TOOL_MAP.get(name)
    if not fn:
        return json.dumps({"error": f"unknown_tool:{name}"})

    try:
        result = fn(**args)
    except Exception as exc:
        result = {"error": f"{type(exc).__name__}: {exc}"}

    return json.dumps(result) if not isinstance(result, str) else result


print("\nSTAGE 5 — GUARDED AGENT LOOP")

order_id = input("Order ID [ORD-48213]: ") or "ORD-48213"
reason = input("Reason [The jug arrived cracked]: ") or "The jug arrived cracked"
requested = float(input("Requested refund [49]: ") or "49")
photo_text = (input("Photo supplied? [yes]: ") or "yes").strip().lower()
photo_supplied = photo_text in {"y", "yes", "true", "1"}

STATE["claim_reason"] = reason
STATE["photo_supplied"] = photo_supplied

system = """
You are a refund operations agent.

Use tools for facts. Never invent order IDs, customer IDs, policy, history,
carrier status, or refund decisions.

Before proposing a refund:
1. verify the order with get_order
2. search the relevant refund policy
3. check refund history
4. for a missing-parcel claim, also check carrier status
5. call propose_refund for the controlled business decision

IMPORTANT:
- You do not have authority to approve or reject refunds in prose.
- A refund outcome exists only if propose_refund returns one.
- After propose_refund returns, explain that tool result briefly.
""".strip()

user_message = f"""
Customer requests a refund.

Order ID: {order_id}
Reason: {reason}
Requested amount: {requested}
Photo supplied: {photo_supplied}

Investigate the claim and use the controlled refund decision tool before giving
a final refund outcome.
""".strip()

messages = [
    {"role": "system", "content": system},
    {"role": "user", "content": user_message},
]

for step in range(1, MAX_STEPS + 1):
    response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
    assistant_message = response.message
    messages.append(assistant_message)

    tool_calls = assistant_message.tool_calls or []

    if tool_calls:
        for call in tool_calls:
            name = call.function.name
            args = dict(call.function.arguments or {})

            print(f"\nSTEP {step} — MODEL REQUEST → {name}")
            print("ARGS:", json.dumps(args))

            # Visible action gate: proposal arguments that represent customer input
            # are rebound to the trusted session inputs before execution.
            if name == "propose_refund":
                rebound = dict(args)
                rebound["order_id"] = order_id
                rebound["requested_amount"] = requested
                rebound["reason"] = reason
                rebound["photo_supplied"] = photo_supplied

                if rebound != args:
                    print("\n⚠ ACTION GATE")
                    print("Rebinding consequential-action arguments to trusted session inputs.")
                    print("MODEL ARGS :", json.dumps(args))
                    print("SAFE ARGS  :", json.dumps(rebound))
                args = rebound

            output = execute_tool(name, args)
            print("OBSERVATION:", output)

            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": output,
                }
            )
        continue

    # The model tried to finish. Do not allow a refund conclusion before the
    # controlled action tool has executed.
    if STATE["proposal_result"] is None:
        print("\n⚠ ACTION GATE")
        print("Model attempted to finish before calling propose_refund.")
        print("No refund outcome is allowed without the controlled decision tool.")
        print("Returning control to the agent.")

        messages.append(
            {
                "role": "user",
                "content": (
                    "ACTION GATE: You have not called propose_refund. "
                    "You may not give a refund outcome yet. "
                    "Call propose_refund using the verified facts."
                ),
            }
        )
        continue

    print("\nFINAL ANSWER")
    print(assistant_message.content)

    # The tool is simulation-only. Make that operational truth explicit even
    # if the LLM's prose accidentally sounds as though money already moved.
    if STATE["proposal_result"].get("simulation_only"):
        print(
            "\nSIMULATION NOTICE: The claim passed the controlled checks, "
            "but no real refund was processed."
        )

    print("\nCONTROLLED OUTCOME")
    print(json.dumps(STATE["proposal_result"], indent=2))
    break
else:
    print("\nSTOP RULE")
    print(f"Agent reached the maximum of {MAX_STEPS} steps.")
    print("Escalate to human review rather than continuing indefinitely.")
