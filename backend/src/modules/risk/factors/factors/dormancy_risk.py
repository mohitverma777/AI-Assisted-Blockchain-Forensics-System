from ..config import WEIGHTS



def score_dormancy_risk(wallet):
    """
    Detects sudden wallet reactivation after prolonged inactivity.
    """

    days_inactive = wallet.get("days_inactive", 0)
    tx_rate = wallet.get("post_reactivation_tx_per_day", 0)

    if days_inactive < 30:
        return 0, "No significant dormancy observed"

    score = 0
    reason = "Dormancy without suspicious reactivation"

    if days_inactive >= 180 and tx_rate >= 20:
        score = 3
        reason = f"Extreme reactivation after long dormancy ({days_inactive} days inactive)"
    elif days_inactive >= 90 and tx_rate >= 10:
        score = 2
        reason = f"Strong reactivation after dormancy ({days_inactive} days inactive)"
    elif days_inactive >= 60 and tx_rate >= 5:
        score = 1
        reason = f"Moderate reactivation after dormancy ({days_inactive} days inactive)"

    max_score = WEIGHTS["dormancy_risk"]
    return min(score, max_score), reason