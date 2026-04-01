from ..config import WEIGHTS



ENTITY_RISK_SCORES = {
    "exchange": 4,
    "bridge": 6,
    "mixer": 10,
    "scam": 12,
    "darknet": 15,
    "sanctioned": 15
}

def score_exposure_risk(wallet):
    """
    Scores wallet based on exposure to known risky entities.
    """

    entities = wallet.get("connected_entities", [])

    if not entities:
        return 0, "No exposure to risky entities detected"

    raw_score = 0
    risky_contacts = []

    for entity in entities:
        risk_type = entity.get("risk_type", "normal")
        score = ENTITY_RISK_SCORES.get(risk_type, 0)

        if score > 0:
            raw_score += score
            risky_contacts.append(risk_type)

    score = 0
    reason = "Low exposure risk"

    if raw_score > 15:
        score = 20
        reason = f"Severe exposure to high-risk entities: {set(risky_contacts)}"
    elif raw_score > 10:
        score = 15
        reason = f"High exposure to risky entities: {set(risky_contacts)}"
    elif raw_score > 5:
        score = 10
        reason = f"Moderate exposure to risky entities: {set(risky_contacts)}"
    elif raw_score > 0:
        score = 5
        reason = f"Light exposure to risky entities: {set(risky_contacts)}"

    max_score = WEIGHTS["exposure_risk"]
    return min(score, max_score), reason
