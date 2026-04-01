import math
from collections import Counter
from ..config import WEIGHTS



def shannon_entropy(values):
    """
    Computes Shannon entropy of a list of values.
    """
    if not values:
        return 0

    total = len(values)
    counts = Counter(values)

    entropy = 0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)

    return entropy


def score_mixing_entropy(wallet):
    """
    Detects mixing / obfuscation behavior using transaction amount entropy.
    """

    amounts = wallet.get("outgoing_amounts", [])

    if len(amounts) < 5:
        return 0, "Insufficient outgoing transactions for entropy analysis"

    entropy = shannon_entropy(amounts)

    score = 0
    reason = "Normal variation in transaction amounts"

    if entropy > 1.5:
        score = 15
        reason = f"High entropy detected (entropy={entropy:.2f}), indicative of mixing behavior"
    elif entropy > 1.0:
        score = 10
        reason = f"Strong uniformity in transaction amounts (entropy={entropy:.2f})"
    elif entropy > 0.5:
        score = 5
        reason = f"Mild uniformity in transaction amounts (entropy={entropy:.2f})"

    max_score = WEIGHTS["mixing_entropy"]
    return min(score, max_score), reason