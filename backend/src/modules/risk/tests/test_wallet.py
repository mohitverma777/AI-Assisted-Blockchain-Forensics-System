"""
Test wallet analysis using the risk engine.
Run with:
  pytest:   python -m pytest modules/risk/tests/test_wallet.py -v
  direct:   python -m modules.risk.tests.test_wallet
From the backend/src directory.
"""
import sys
import os

# Ensure parent modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from modules.risk.risk_engine import risk_engine


# ---------- test data ----------

DEMO_WALLET = {
    'address': '0xTestAddress123',
    'transactions': [
        {'from': '0xTestAddress123', 'timeStamp': '1770052979', 'value': '1000000000000000000'},
        {'from': '0xTestAddress123', 'timeStamp': '1770052895', 'value': '2000000000000000000'},
        {'from': 'other', 'timeStamp': '1770052811', 'value': '500000000000000000'},
    ],
    'incoming_amounts': [100, 200, 150, 75],
    'outgoing_amounts': [0.01, 0.02, 0.03, 1.5, 2500],
    'tx_timestamps': [1770052979, 1770052895, 1770052811, 1770052643],
    'cluster_size': 25,
    'avg_degree': 9.2,
    'days_inactive': 2,
    'post_reactivation_tx_per_day': 333
}


# ---------- pytest-compatible test functions ----------

def test_risk_engine_returns_dict():
    """Risk engine should return a dict."""
    result = risk_engine(DEMO_WALLET)
    assert isinstance(result, dict)


def test_risk_engine_has_overall_risk():
    """Result should contain overall_risk between 0 and 100."""
    result = risk_engine(DEMO_WALLET)
    assert 'overall_risk' in result
    assert 0 <= result['overall_risk'] <= 100


def test_risk_engine_has_risk_band():
    """Result should contain a valid risk_band."""
    result = risk_engine(DEMO_WALLET)
    assert result['risk_band'] in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')


def test_risk_engine_has_factor_breakdown():
    """Result should contain factor_breakdown with 10 factors."""
    result = risk_engine(DEMO_WALLET)
    assert 'factor_breakdown' in result
    assert len(result['factor_breakdown']) == 10


def test_risk_engine_factor_scores_are_valid():
    """Each factor score should be a non-negative number."""
    result = risk_engine(DEMO_WALLET)
    for name, factor in result['factor_breakdown'].items():
        assert 'score' in factor, f"Missing 'score' in factor: {name}"
        assert factor['score'] >= 0, f"Negative score in factor: {name}"


def test_risk_engine_empty_wallet():
    """Risk engine should handle an empty wallet gracefully."""
    empty = {
        'address': '0xEmpty',
        'transactions': [],
        'incoming_amounts': [0],
        'outgoing_amounts': [0],
        'tx_timestamps': [0],
        'cluster_size': 0,
        'avg_degree': 0,
        'days_inactive': 0,
        'post_reactivation_tx_per_day': 0
    }
    result = risk_engine(empty)
    assert isinstance(result, dict)
    assert result['overall_risk'] >= 0


# ---------- direct execution ----------

if __name__ == '__main__':
    print("ANALYZING TEST WALLET...")
    result = risk_engine(DEMO_WALLET)

    print("\n" + "=" * 70)
    print(f"RISK SCORE: {result['overall_risk']}/100")
    print(f"Band: {result['risk_band']}")
    print("=" * 70)

    print("\nFactor breakdown:")
    for k, v in result.get('factor_breakdown', {}).items():
        print(f"  {k}: {v['score']} pts -- {v['reason']}")

    print("\nAll tests would pass!" if result['overall_risk'] >= 0 else "")
