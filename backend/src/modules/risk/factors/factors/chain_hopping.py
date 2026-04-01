from ..config import WEIGHTS



def score_chain_hopping(wallet):
    """
    Detects layering via long transaction paths.
    """

    avg_path_length = wallet.get("avg_path_length", 0)

    if avg_path_length <= 0:
        return 0, "Insufficient path data"

    score = 0
    reason = "Direct or short transaction paths observed"

    if avg_path_length > 6:
        score = 3
        reason = f"Excessive chain hopping detected (avg hops ≈ {avg_path_length:.1f})"
    elif avg_path_length > 4:
        score = 2
        reason = f"Multiple intermediate hops detected (avg hops ≈ {avg_path_length:.1f})"
    elif avg_path_length > 2:
        score = 1
        reason = f"Moderate chain hopping observed (avg hops ≈ {avg_path_length:.1f})"

    max_score = WEIGHTS["chain_hopping"]
    return min(score, max_score), reason
