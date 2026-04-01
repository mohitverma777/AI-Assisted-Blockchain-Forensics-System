import statistics
from ..config import WEIGHTS



def score_behavioral_pattern(wallet):
    """
    Detects automated or scripted transaction timing patterns.
    """

    timestamps = wallet.get("tx_timestamps", [])

    if len(timestamps) < 4:
        return 0, "Insufficient transaction history for timing analysis"

    # Sort timestamps
    timestamps = sorted(timestamps)

    # Compute time gaps between consecutive transactions
    time_gaps = [
        timestamps[i] - timestamps[i - 1]
        for i in range(1, len(timestamps))
    ]

    if len(time_gaps) < 2:
        return 0, "Insufficient timing gaps"

    std_dev = statistics.stdev(time_gaps)

    score = 0
    reason = "Irregular transaction timing (human-like behavior)"

    if std_dev < 300:  # < 5 minutes
        score = 10
        reason = "Highly regular transaction timing (automated behavior)"
    elif std_dev < 1800:  # < 30 minutes
        score = 7
        reason = "Strongly regular transaction timing pattern detected"
    elif std_dev < 7200:  # < 2 hours
        score = 4
        reason = "Mild regularity in transaction timing"

    max_score = WEIGHTS["behavioral_pattern"]
    return min(score, max_score), reason