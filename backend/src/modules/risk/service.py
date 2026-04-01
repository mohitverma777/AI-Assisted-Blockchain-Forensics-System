from .risk_engine import risk_engine
from .etherscan_api import fetch_wallet_data

def analyze_wallet(address: str):
    api_data = fetch_wallet_data(address)

    wallet = build_wallet_object(address, api_data)

    result = risk_engine(wallet)

    return {
        "risk_score": result["overall_risk"],
        "risk_band": result["risk_band"],
        "risk_color": result["risk_color"],
        "factor_breakdown": result["factor_breakdown"],
        "top_factors": result["top_factors"],
        "investigation_leads": result["investigation_leads"],
        "metrics": {
            "total_transactions": wallet["total_transactions"],
            "total_volume": sum(wallet["incoming_amounts"]),
            "connected_wallets": wallet["cluster_size"],
            "suspicious_activities": len(result["investigation_leads"])
        }
    }
