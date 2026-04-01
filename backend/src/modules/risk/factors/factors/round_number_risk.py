from ..config import WEIGHTS



def score_round_number_risk(wallet):
    """
    Detects suspicious usage of round-number transaction amounts.
    """

    txns = wallet.get("transactions", [])
    outgoing = [tx for tx in txns if tx["from"] == wallet["address"]]

    if not outgoing:
        return 0, "No outgoing transactions"

    round_count = 0

    for tx in outgoing:
        value = float(tx["value"])
        if round(value, 3) == value:
            round_count += 1

    ratio = round_count / len(outgoing)
    score = 0

    if ratio > 0.8:
        score = 4
    elif ratio > 0.6:
        score = 3
    elif ratio > 0.4:
        score = 2
    elif ratio > 0.2:
        score = 1

    return score, f"{round_count}/{len(outgoing)} transactions have round-number amounts"