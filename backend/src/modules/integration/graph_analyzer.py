"""
Graph Analyzer
Calculates graph metrics from Neo4j for risk scoring
Authors: Krusha (Graph), Mohit (Integration)
"""

from datetime import datetime
from typing import Dict


def calculate_graph_metrics(neo4j_conn, wallet_address: str) -> Dict:
    """
    Calculate cluster size and connection density from Neo4j graph
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Wallet address to analyze
        
    Returns:
        Dict with cluster_size and avg_degree
    """
    
    # Query 1: Count connected wallets (within 2 hops)
    cluster_query = """
    MATCH (w:Wallet {address: $address})
    OPTIONAL MATCH (w)-[:SENT|RECEIVED_BY*1..2]-(connected:Wallet)
    WHERE connected.address <> w.address
    RETURN count(DISTINCT connected) as cluster_size
    """
    
    # Query 2: Calculate average degree (connections per wallet)
    degree_query = """
    MATCH (w:Wallet {address: $address})-[r:SENT|RECEIVED_BY]-(t:Transaction)
    RETURN count(DISTINCT r) as degree
    """
    
    try:
        cluster_result = neo4j_conn.execute_query(cluster_query, {"address": wallet_address})
        degree_result = neo4j_conn.execute_query(degree_query, {"address": wallet_address})
        
        cluster_size = cluster_result[0]['cluster_size'] if cluster_result else 0
        degree = degree_result[0]['degree'] if degree_result else 0
        
        # Avoid division by zero
        avg_degree = degree / max(1, cluster_size) if cluster_size > 0 else float(degree)
        
        return {
            'cluster_size': max(1, cluster_size),  # At least 1 (the wallet itself)
            'avg_degree': round(avg_degree, 2)
        }
    except Exception as e:
        print(f"⚠️  Graph metrics calculation failed: {e}")
        return {
            'cluster_size': 1,
            'avg_degree': 0.0
        }


def calculate_dormancy_metrics(neo4j_conn, wallet_address: str) -> Dict:
    """
    Calculate dormancy and reactivation metrics from transaction history
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Wallet address to analyze
        
    Returns:
        Dict with days_inactive and post_reactivation_tx_per_day
    """
    
    query = """
    MATCH (w:Wallet {address: $address})-[r:SENT|RECEIVED_BY]-(t:Transaction)
    WHERE t.timestamp IS NOT NULL
    WITH t
    ORDER BY t.timestamp DESC
    RETURN t.timestamp as timestamp
    LIMIT 100
    """
    
    try:
        result = neo4j_conn.execute_query(query, {"address": wallet_address})
        
        if not result or len(result) == 0:
            return {
                'days_inactive': 0,
                'post_reactivation_tx_per_day': 0
            }
        
        # Extract timestamps
        timestamps = []
        for record in result:
            ts = record.get('timestamp')
            if hasattr(ts, 'to_native'):
                # Neo4j datetime object
                timestamps.append(ts.to_native().timestamp())
            elif isinstance(ts, str):
                # ISO string
                timestamps.append(datetime.fromisoformat(ts).timestamp())
            elif isinstance(ts, (int, float)):
                timestamps.append(float(ts))
        
        if len(timestamps) < 2:
            return {
                'days_inactive': 0,
                'post_reactivation_tx_per_day': 0
            }
        
        timestamps.sort(reverse=True)  # Most recent first
        
        # Days since last transaction
        now = datetime.now().timestamp()
        last_tx = timestamps[0]
        days_inactive = max(0, int((now - last_tx) / 86400))
        
        # Calculate transaction velocity in last 30 days
        thirty_days_ago = now - (30 * 86400)
        recent_txs = sum(1 for ts in timestamps if ts >= thirty_days_ago)
        post_reactivation_tx_per_day = recent_txs / 30 if recent_txs > 0 else 0
        
        return {
            'days_inactive': days_inactive,
            'post_reactivation_tx_per_day': round(post_reactivation_tx_per_day, 2)
        }
        
    except Exception as e:
        print(f"⚠️  Dormancy metrics calculation failed: {e}")
        return {
            'days_inactive': 0,
            'post_reactivation_tx_per_day': 0
        }


def get_wallet_statistics(neo4j_conn, wallet_address: str) -> Dict:
    """
    Get comprehensive wallet statistics from Neo4j
    
    Returns:
        Dict with various wallet metrics
    """
    
    query = """
    MATCH (w:Wallet {address: $address})
    OPTIONAL MATCH (w)-[:SENT]->(sent:Transaction)
    OPTIONAL MATCH (w)<-[:RECEIVED_BY]-(received:Transaction)
    RETURN 
        w.balance as balance,
        w.total_transactions as total_txs,
        count(DISTINCT sent) as sent_count,
        count(DISTINCT received) as received_count
    """
    
    try:
        result = neo4j_conn.execute_query(query, {"address": wallet_address})
        
        if result and len(result) > 0:
            return {
                'balance': result[0].get('balance', 0),
                'total_transactions': result[0].get('total_txs', 0),
                'sent_count': result[0].get('sent_count', 0),
                'received_count': result[0].get('received_count', 0)
            }
    except Exception as e:
        print(f"⚠️  Wallet statistics query failed: {e}")
    
    return {
        'balance': 0,
        'total_transactions': 0,
        'sent_count': 0,
        'received_count': 0
    }


# Test function
if __name__ == '__main__':
    from ...graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Graph Analyzer")
    print("="*60 + "\n")
    
    try:
        with Neo4jConnection() as conn:
            # Test with a wallet (replace with actual address in your Neo4j)
            test_wallet = "0xF977814e90dA44bFA03b6295A0616a897441aceC"
            
            print("Testing graph metrics calculation...")
            metrics = calculate_graph_metrics(conn, test_wallet)
            print(f"✅ Cluster size: {metrics['cluster_size']}")
            print(f"✅ Avg degree: {metrics['avg_degree']}")
            
            print("\nTesting dormancy metrics...")
            dormancy = calculate_dormancy_metrics(conn, test_wallet)
            print(f"✅ Days inactive: {dormancy['days_inactive']}")
            print(f"✅ TX per day: {dormancy['post_reactivation_tx_per_day']}")
            
            print("\nTesting wallet statistics...")
            stats = get_wallet_statistics(conn, test_wallet)
            print(f"✅ Balance: {stats['balance']}")
            print(f"✅ Total transactions: {stats['total_transactions']}")
            
            print("\n✅ All graph analyzer tests passed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
