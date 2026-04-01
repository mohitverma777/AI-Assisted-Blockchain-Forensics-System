from ..config import WEIGHTS



def score_amount_anomaly(wallet):
    """
    Detects smurfing / structuring behavior.
    Small incoming amounts followed by large outgoing transfers.
    """

    incoming = wallet.get("incoming_amounts", [])
    outgoing = wallet.get("outgoing_amounts", [])

    if not incoming or not outgoing:
        return 0, "Insufficient transaction data"

    avg_in = sum(incoming) / len(incoming)
    max_out = max(outgoing)

    if avg_in == 0:
        return 0, "Invalid incoming amounts"

    ratio = max_out / avg_in

    score = 0
    reason = "No significant amount anomaly"

    if ratio > 100:
        score = 15
        reason = f"Extreme amount anomaly: large outflow ({max_out:.4f}) vs small inflow avg ({avg_in:.4f})"
    elif ratio > 50:
        score = 10
        reason = f"Strong amount anomaly detected (ratio ≈ {ratio:.1f})"
    elif ratio > 10:
        score = 5
        reason = f"Mild amount anomaly detected (ratio ≈ {ratio:.1f})"

    max_score = WEIGHTS["amount_anomaly"]
    return min(score, max_score), reason