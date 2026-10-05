"""Shared deterministic refund decision logic used by workshop evals."""


def decide_refund(amount_paid, requested, claim_type, photo_supplied, refunds_last_12m):
    """Apply non-negotiable business controls in deterministic code."""
    if requested > amount_paid:
        return "BLOCKED"
    if requested > 200:
        return "HUMAN_REVIEW"
    if requested > 75:
        return "HUMAN_REVIEW"
    if claim_type == "DAMAGED_ITEM" and not photo_supplied:
        return "NEEDS_INFORMATION"
    if refunds_last_12m >= 3:
        return "HUMAN_REVIEW"
    return "AUTO_APPROVE"
