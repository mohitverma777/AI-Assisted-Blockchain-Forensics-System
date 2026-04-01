WEIGHTS = {
    'transaction_velocity': 15,
    'amount_anomaly': 15, 
    'behavioral_pattern': 10,
    'connection_density': 12,
    'dormancy_risk': 10,
    'mixing_entropy': 12,
    'exposure_risk': 8,
    'chain_hopping': 8,
    'peeling_chain': 15,
    'round_number_risk': 5
}

RISK_BANDS = {
    (0, 25): ('LOW', '🟢'),
    (26, 50): ('MEDIUM', '🟡'),
    (51, 75): ('HIGH', '🟠'),
    (76, 100): ('CRITICAL', '🔴')
}
