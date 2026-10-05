"""Stage 6: deterministic golden-case evaluation.

These tests intentionally avoid the LLM. We are measuring the hard decision
layer independently so failures are repeatable and easy to diagnose.
"""

from pathlib import Path
import json
from decision import decide_refund

HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / "golden_cases.json").read_text())

print("\nSTAGE 6 — GOLDEN-CASE EVALS")
passed = 0

for case in cases:
    actual = decide_refund(
        amount_paid=case["amount_paid"],
        requested=case["requested"],
        claim_type=case["claim_type"],
        photo_supplied=case["photo_supplied"],
        refunds_last_12m=case["refunds_last_12m"],
    )
    ok = actual == case["expected"]
    passed += int(ok)
    status = "PASS" if ok else "FAIL"
    print(
        f"{status} | {case['name']} | "
        f"expected={case['expected']} got={actual}"
    )

print(f"\nRESULT: {passed}/{len(cases)} passed")
