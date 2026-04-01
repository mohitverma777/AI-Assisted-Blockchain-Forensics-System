from risk_engine.config import WEIGHTS, RISK_BANDS

from risk_engine.factors.transaction_velocity import score_transaction_velocity
from risk_engine.factors.amount_anomaly import score_amount_anomaly
from risk_engine.factors.connection_density import score_connection_density
from risk_engine.factors.behavioral_pattern import score_behavioral_pattern
from risk_engine.factors.entropy import score_entropy
from risk_engine.factors.exposure_risk import score_exposure_risk
from risk_engine.factors.chain_hopping import score_chain_hopping
from risk_engine.factors.dormancy_risk import score_dormancy_risk
from risk_engine.factors.round_number_risk import score_round_number_risk
from risk_engine.factors.peeling_chain import score_peeling_chain


def get_risk_band(score):
    for (low, high), (label, color) in RISK_BANDS.items():
        if low <= score <= high:
            return label, color
    return "UNKNOWN", "#6c757d"


def calculate_wallet_risk(wallet):
    breakdown = {}
    reasons = {}
    total_score = 0

    factor_functions = {
        "transaction_velocity": score_transaction_velocity,
        "amount_anomaly": score_amount_anomaly,
        "connection_density": score_connection_density,
        "behavioral_pattern": score_behavioral_pattern,
        "exposure_risk": score_exposure_risk,
        "mixing_entropy": score_entropy,
        "chain_hopping": score_chain_hopping,
        "dormancy_risk": score_dormancy_risk,
        "round_number_risk": score_round_number_risk,
        "peeling_chain": score_peeling_chain
    }

    for factor, func in factor_functions.items():
        score, reason = func(wallet)
        breakdown[factor] = score
        reasons[factor] = reason
        total_score += score

    total_score = min(100, total_score)
    risk_band, color = get_risk_band(total_score)

    return {
        "wallet": wallet["address"],
        "total_score": total_score,
        "risk_band": risk_band,
        "color": color,
        "breakdown": breakdown,
        "reasons": reasons
    }
