from ..config import WEIGHTS



def score_connection_density(wallet):
    """
    Detects tightly connected wallet clusters indicating shared control.
    """

    cluster_size = wallet.get("cluster_size", 0)
    avg_degree = wallet.get("avg_degree", 0)

    if cluster_size <= 1:
        return 0, "Isolated or minimal wallet connections"

    score = 0
    reason = "Sparse wallet connections"

    if cluster_size >= 20 and avg_degree >= 8:
        score = 10
        reason = f"Highly dense wallet cluster detected (size={cluster_size}, avg_degree={avg_degree:.1f})"
    elif cluster_size >= 10 and avg_degree >= 5:
        score = 7
        reason = f"Dense wallet cluster detected (size={cluster_size}, avg_degree={avg_degree:.1f})"
    elif cluster_size >= 5 and avg_degree >= 3:
        score = 4
        reason = f"Moderate wallet clustering observed (size={cluster_size}, avg_degree={avg_degree:.1f})"

    max_score = WEIGHTS["connection_density"]
    return min(score, max_score), reason