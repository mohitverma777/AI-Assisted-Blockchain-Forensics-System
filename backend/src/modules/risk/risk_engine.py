from typing import Dict, List
from .config import WEIGHTS, RISK_BANDS

from .factors.transaction_velocity import score_transaction_velocity
from .factors.amount_anomaly import score_amount_anomaly
from .factors.behavioral_pattern import score_behavioral_pattern
from .factors.connection_density import score_connection_density
from .factors.dormancy_risk import score_dormancy_risk
from .factors.entropy import score_mixing_entropy
from .factors.exposure_risk import score_exposure_risk
from .factors.chain_hopping import score_chain_hopping
from .factors.peeling_chain import score_peeling_chain
from .factors.round_number_risk import score_round_number_risk

def risk_engine(wallet: Dict) -> Dict:
    '''Module D: Combines ALL 10 factors → 0-100 risk score'''
    
    # Run all 10 forensic factors
    factor_results = {
        'transaction_velocity': score_transaction_velocity(wallet),
        'amount_anomaly': score_amount_anomaly(wallet),
        'behavioral_pattern': score_behavioral_pattern(wallet),
        'connection_density': score_connection_density(wallet),
        'dormancy_risk': score_dormancy_risk(wallet),
        'mixing_entropy': score_mixing_entropy(wallet),
        'exposure_risk': score_exposure_risk(wallet),
        'chain_hopping': score_chain_hopping(wallet),
        'peeling_chain': score_peeling_chain(wallet),
        'round_number_risk': score_round_number_risk(wallet)
    }
    
    # Calculate total 0-100 score
    total_score = sum(score for score, _ in factor_results.values())
    
    # Risk band
    risk_band, risk_color = next(
        (band, color) for (low, high), (band, color) in RISK_BANDS.items()
        if low <= total_score <= high
    )
    
    # Top 3 factors + investigation leads
    top_factors = sorted(
        factor_results.items(), 
        key=lambda x: x[1][0], reverse=True
    )[:3]
    
    leads = generate_investigation_leads(factor_results, total_score)
    
    return {
        'overall_risk': round(total_score),
        'risk_band': risk_band,
        'risk_color': risk_color,
        'factor_breakdown': {k: {'score': v[0], 'reason': v[1]} for k, v in factor_results.items()},
        'top_factors': [f'{k}: {v[0]}/{WEIGHTS[k]}pts' for k, v in top_factors],
        'investigation_leads': leads
    }

def generate_investigation_leads(factors: Dict, total_score: float) -> List[str]:
    leads = []
    scores = {k: v[0] for k, v in factors.items()}
    
    if scores['peeling_chain'] >= 3 or total_score > 70:
        leads.append('🔴 FIU-IND: Subpoena WazirX/CoinDCX (90% hit rate)')
    if scores['mixing_entropy'] >= 10:
        leads.append('🕵️ Twitter/Telegram OSINT: wallet address')
    if scores['amount_anomaly'] >= 10:
        leads.append('💰 ITD Form 26Q: Undeclared VDA gains > ₹10L')
    
    return leads[:3]

if __name__ == '__main__':
    # Demo high-risk wallet
    demo_wallet = {
        'address': '1BvUMse1234567890',
        'transactions': [{'from':'test','timeStamp':'1640995200'}, {'from':'test','timeStamp':'1641081600'}],
        'incoming_amounts': [0.01,0.02,0.03], 
        'outgoing_amounts': [1.5],
        'tx_timestamps': [1640995200,1640995500,1640995800,1640996100],
        'cluster_size': 25, 'avg_degree': 9.2,
        'days_inactive': 200, 'post_reactivation_tx_per_day': 25
    }
    
    result = risk_engine(demo_wallet)
    print(f'🎯 FINAL RESULT: {result['overall_risk']}/100 ({result['risk_band']})')
    print('Top factors:', result['top_factors'])
    print('Investigation leads:', result['investigation_leads'])
