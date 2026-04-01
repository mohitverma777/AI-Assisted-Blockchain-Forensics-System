# Open factors/transaction_velocity.py and change line 1 to:
from ..config import WEIGHTS




SECONDS_IN_DAY = 86400

def score_transaction_velocity(wallet):
    """
    Scores transaction velocity based on outgoing txns per active day.
    """

    txns = wallet.get("transactions", [])
    outgoing = [tx for tx in txns if tx.get("from", "") == wallet.get("address", "")]

    if len(outgoing) < 2:
        return 0, "Insufficient transactions for velocity analysis"

    timestamps = sorted(int(tx.get("timeStamp", 0)) for tx in outgoing if tx.get("timeStamp"))

    active_days = max(1, (timestamps[-1] - timestamps[0]) / SECONDS_IN_DAY)
    velocity = len(outgoing) / active_days

    if velocity > 10:
        score = 15
    elif velocity > 5:
        score = 10
    elif velocity > 2:
        score = 5
    else:
        score = 0

    reason = f"{len(outgoing)} outgoing txns over {active_days:.1f} days ({velocity:.2f} txns/day)"
    return score, reason
