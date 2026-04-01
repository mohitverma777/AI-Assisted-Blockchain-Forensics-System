from ..config import WEIGHTS



def score_peeling_chain(wallet):
    """
    Detects peeling chain behavior:
    Large incoming amount followed by sequential smaller outgoing txns.
    """

    txns = wallet.get("transactions", [])

    # Filter outgoing transactions
    outgoing = [tx for tx in txns if tx["from"] == wallet["address"]]

    if len(outgoing) < 3:
        return 0, "Not enough outgoing transactions for peeling pattern"

    # Sort by time
    outgoing.sort(key=lambda x: x["timestamp"])

    peel_count = 0

    for i in range(1, len(outgoing)):
        prev = outgoing[i - 1]["value"]
        curr = outgoing[i]["value"]

        if curr < prev:
            peel_count += 1
        else:
            peel_count = 0  # reset if pattern breaks

    score = 0
    reason = "No peeling chain detected"

    if peel_count >= 5:
        score = 15
        reason = f"Strong peeling chain detected ({peel_count + 1} sequential decreasing transfers)"
    elif peel_count >= 3:
        score = 10
        reason = f"Moderate peeling chain detected ({peel_count + 1} decreasing transfers)"
    elif peel_count >= 2:
        score = 5
        reason = f"Weak peeling chain detected ({peel_count + 1} decreasing transfers)"

    max_score = WEIGHTS["peeling_chain"]
    return min(score, max_score), reason