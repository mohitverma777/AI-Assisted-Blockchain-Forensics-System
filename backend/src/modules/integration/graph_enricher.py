"""
Graph Enricher
Adds risk analysis results back to Neo4j Wallet nodes
Authors: Krusha (Graph), Mohit (Integration)
"""

from typing import Dict


def enrich_wallet_with_risk(neo4j_conn, wallet_address: str, risk_result: Dict) -> bool:
    """
    Add risk analysis results to Wallet node in Neo4j
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Wallet address
        risk_result: Output from risk_engine()
        
    Returns:
        bool: True if successful
    """
    
    query = """
    MATCH (w:Wallet {address: $address})
    SET w.risk_score = $risk_score,
        w.risk_level = $risk_level,
        w.risk_color = $risk_color,
        w.top_risk_factors = $top_factors,
        w.investigation_leads = $leads,
        w.risk_updated = datetime()
    RETURN w.address as address, w.risk_score as score
    """
    
    try:
        # Extract risk data
        parameters = {
            "address": wallet_address,
            "risk_score": risk_result.get('overall_risk', 0),
            "risk_level": risk_result.get('risk_band', 'UNKNOWN'),
            "risk_color": risk_result.get('risk_color', '⚪'),
            "top_factors": risk_result.get('top_factors', []),
            "leads": risk_result.get('investigation_leads', [])
        }
        
        result = neo4j_conn.execute_query(query, parameters)
        
        if result and len(result) > 0:
            print(f"✅ Enriched wallet {wallet_address[:10]}... with risk score: {parameters['risk_score']}")
            return True
        else:
            print(f"⚠️  Wallet not found in Neo4j: {wallet_address}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to enrich wallet with risk data: {e}")
        import traceback
        traceback.print_exc()
        return False


def enrich_wallet_with_factor_breakdown(neo4j_conn, wallet_address: str, factor_breakdown: Dict) -> bool:
    """
    Add detailed factor breakdown to wallet (optional, for detailed analysis)
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Wallet address
        factor_breakdown: Dict of {factor_name: {'score': X, 'reason': 'Y'}}
        
    Returns:
        bool: True if successful
    """
    
    # Convert factor breakdown to simpler format for Neo4j
    factor_scores = {}
    factor_reasons = {}
    
    for factor_name, data in factor_breakdown.items():
        factor_scores[factor_name] = data.get('score', 0)
        factor_reasons[factor_name] = data.get('reason', '')
    
    query = """
    MATCH (w:Wallet {address: $address})
    SET w.factor_scores = $factor_scores,
        w.factor_reasons = $factor_reasons
    RETURN w.address as address
    """
    
    try:
        parameters = {
            "address": wallet_address,
            "factor_scores": factor_scores,
            "factor_reasons": factor_reasons
        }
        
        result = neo4j_conn.execute_query(query, parameters)
        
        if result and len(result) > 0:
            print(f"✅ Added detailed factor breakdown to wallet")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"⚠️  Failed to add factor breakdown: {e}")
        return False


def query_wallets_by_risk_level(neo4j_conn, risk_level: str = None, min_score: int = None):
    """
    Query wallets by risk level or minimum score
    
    Args:
        neo4j_conn: Neo4jConnection instance
        risk_level: "LOW", "MEDIUM", "HIGH", or "CRITICAL"
        min_score: Minimum risk score (0-100)
        
    Returns:
        List of wallet records
    """
    
    if risk_level:
        query = """
        MATCH (w:Wallet)
        WHERE w.risk_level = $risk_level
        RETURN w.address, w.blockchain, w.risk_score, w.risk_level, w.top_risk_factors
        ORDER BY w.risk_score DESC
        """
        result = neo4j_conn.execute_query(query, {"risk_level": risk_level})
        
    elif min_score is not None:
        query = """
        MATCH (w:Wallet)
        WHERE w.risk_score >= $min_score
        RETURN w.address, w.blockchain, w.risk_score, w.risk_level, w.top_risk_factors
        ORDER BY w.risk_score DESC
        """
        result = neo4j_conn.execute_query(query, {"min_score": min_score})
        
    else:
        query = """
        MATCH (w:Wallet)
        WHERE w.risk_score IS NOT NULL
        RETURN w.address, w.blockchain, w.risk_score, w.risk_level, w.top_risk_factors
        ORDER BY w.risk_score DESC
        """
        result = neo4j_conn.execute_query(query)
    
    return result


def get_risk_distribution(neo4j_conn) -> Dict:
    """
    Get distribution of wallets by risk level
    
    Returns:
        Dict with counts per risk level
    """
    
    query = """
    MATCH (w:Wallet)
    WHERE w.risk_level IS NOT NULL
    RETURN w.risk_level as level, count(w) as count, avg(w.risk_score) as avg_score
    ORDER BY avg_score DESC
    """
    
    try:
        result = neo4j_conn.execute_query(query)
        
        distribution = {}
        for record in result:
            level = record.get('level', 'UNKNOWN')
            distribution[level] = {
                'count': record.get('count', 0),
                'avg_score': round(record.get('avg_score', 0), 2)
            }
        
        return distribution
        
    except Exception as e:
        print(f"⚠️  Failed to get risk distribution: {e}")
        return {}


# Test function
if __name__ == '__main__':
    from ...graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Graph Enricher")
    print("="*60 + "\n")
    
    # Sample risk result
    sample_risk = {
        'overall_risk': 65,
        'risk_band': 'HIGH',
        'risk_color': '🟠',
        'top_factors': [
            'transaction_velocity: 12/15pts',
            'peeling_chain: 10/15pts',
            'mixing_entropy: 8/12pts'
        ],
        'investigation_leads': [
            '🔴 FIU-IND: Subpoena WazirX/CoinDCX',
            '🕵️ Twitter/Telegram OSINT'
        ],
        'factor_breakdown': {
            'transaction_velocity': {'score': 12, 'reason': 'High velocity'},
            'peeling_chain': {'score': 10, 'reason': 'Suspicious pattern'}
        }
    }
    
    try:
        with Neo4jConnection() as conn:
            test_wallet = "0xF977814e90dA44bFA03b6295A0616a897441aceC"
            
            print("Testing risk enrichment...")
            success = enrich_wallet_with_risk(conn, test_wallet, sample_risk)
            
            if success:
                print("\nQuerying risk distribution...")
                distribution = get_risk_distribution(conn)
                for level, data in distribution.items():
                    print(f"   {level}: {data['count']} wallets (avg: {data['avg_score']})")
                
                print("\n✅ All graph enricher tests passed!")
            else:
                print("⚠️  Wallet not in Neo4j - run blockchain fetcher first")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
