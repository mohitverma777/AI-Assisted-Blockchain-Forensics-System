from ..config import WEIGHTS



def score_peeling_chain(wallet):
    """
    Detects peeling chain behavior:
    Large incoming amount followed by sequential smaller outgoing txns.
    """

    txns = wallet.get("transactions", [])

    # Filter outgoing transactions (defensive .get() for missing keys)
    outgoing = [tx for tx in txns if tx.get("from", "") == wallet.get("address", "")]

    if len(outgoing) < 3:
        return 0, "Not enough outgoing transactions for peeling pattern"

    # Sort by time — support both 'timeStamp' (Etherscan) and 'timestamp'
    outgoing.sort(key=lambda x: int(x.get("timeStamp", x.get("timestamp", 0))))

    peel_count = 0

    for i in range(1, len(outgoing)):
        try:
            prev = float(outgoing[i - 1].get("value", 0))
            curr = float(outgoing[i].get("value", 0))
        except (ValueError, TypeError):
            continue

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