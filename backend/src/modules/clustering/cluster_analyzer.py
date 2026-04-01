"""
Cluster Analyzer
Quality metrics and risk aggregation for wallet clusters
Authors: Mohit (Analysis), Team (Support)
"""

from typing import Dict, List
import numpy as np


def aggregate_cluster_risk(neo4j_conn, cluster_id: str) -> Dict:
    """
    Aggregate risk metrics for a cluster
    
    Returns:
        Dict with cluster risk assessment
    """
    
    query = """
    MATCH (c:Cluster {cluster_id: $cluster_id})<-[:BELONGS_TO]-(w:Wallet)
    WHERE w.risk_score IS NOT NULL
    
    WITH c,
         count(w) as total_wallets,
         avg(w.risk_score) as avg_risk,
         max(w.risk_score) as max_risk,
         min(w.risk_score) as min_risk,
         stdev(w.risk_score) as risk_std,
         collect(w.risk_level) as risk_levels,
         sum(w.balance) as total_balance
    
    RETURN total_wallets,
           avg_risk,
           max_risk,
           min_risk,
           risk_std,
           risk_levels,
           total_balance
    """
    
    try:
        result = neo4j_conn.execute_query(query, {'cluster_id': cluster_id})
        
        if result and len(result) > 0:
            data = result[0]
            
            # Count risk levels
            risk_levels = data.get('risk_levels', [])
            high_risk_count = sum(1 for level in risk_levels if level in ['HIGH', 'CRITICAL'])
            
            # Calculate cluster priority
            avg_risk = data.get('avg_risk', 0)
            max_risk = data.get('max_risk', 0)
            
            # Priority = weighted combination
            priority_score = (avg_risk * 0.6) + (max_risk * 0.4)
            
            if max_risk >= 80 or high_risk_count >= 3:
                priority = "CRITICAL"
            elif avg_risk >= 60 or max_risk >= 70:
                priority = "HIGH"
            elif avg_risk >= 40:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            
            return {
                'cluster_id': cluster_id,
                'total_wallets': data['total_wallets'],
                'avg_risk_score': round(data.get('avg_risk', 0), 2),
                'max_risk_score': data.get('max_risk', 0),
                'min_risk_score': data.get('min_risk', 0),
                'risk_std': round(data.get('risk_std', 0), 2),
                'high_risk_wallet_count': high_risk_count,
                'total_balance': data.get('total_balance', 0),
                'priority': priority,
                'priority_score': round(priority_score, 2)
            }
        
        return {}
        
    except Exception as e:
        print(f"⚠️  Failed to aggregate cluster risk: {e}")
        return {}


def find_inter_cluster_transactions(neo4j_conn, min_transactions: int = 5) -> List[Dict]:
    """
    Find significant transaction flows between clusters
    
    Args:
        neo4j_conn: Neo4jConnection instance
        min_transactions: Minimum transactions to report
        
    Returns:
        List of inter-cluster transaction info
    """
    
    query = """
    MATCH (c1:Cluster)<-[:BELONGS_TO]-(w1:Wallet)
    MATCH (c2:Cluster)<-[:BELONGS_TO]-(w2:Wallet)
    MATCH (w1)-[:SENT]->(t:Transaction)-[:RECEIVED_BY]->(w2)
    WHERE c1.cluster_id < c2.cluster_id  // Avoid duplicates
    
    WITH c1, c2, 
         count(t) as tx_count,
         sum(t.value) as total_value
    WHERE tx_count >= $min_txs
    
    RETURN c1.cluster_id as cluster1,
           c2.cluster_id as cluster2,
           c1.avg_risk_score as cluster1_risk,
           c2.avg_risk_score as cluster2_risk,
           tx_count,
           total_value
    ORDER BY tx_count DESC
    LIMIT 20
    """
    
    try:
        result = neo4j_conn.execute_query(query, {'min_txs': min_transactions})
        
        inter_cluster_txs = []
        for record in result:
            inter_cluster_txs.append({
                'cluster1_id': record['cluster1'],
                'cluster2_id': record['cluster2'],
                'cluster1_risk': round(record.get('cluster1_risk', 0), 2),
                'cluster2_risk': round(record.get('cluster2_risk', 0), 2),
                'transaction_count': record['tx_count'],
                'total_value': record.get('total_value', 0),
                'is_high_risk_flow': (
                    record.get('cluster1_risk', 0) >= 60 or 
                    record.get('cluster2_risk', 0) >= 60
                )
            })
        
        return inter_cluster_txs
        
    except Exception as e:
        print(f"⚠️  Failed to find inter-cluster transactions: {e}")
        return []


def analyze_cluster_quality(cluster_wallets: List[str], feature_matrix: np.ndarray, labels: np.ndarray) -> Dict:
    """
    Calculate clustering quality metrics
    
    Args:
        cluster_wallets: List of wallet addresses
        feature_matrix: Feature matrix used for clustering
        labels: Cluster labels
        
    Returns:
        Dict with quality metrics
    """
    
    try:
        from sklearn.metrics import silhouette_score, davies_bouldin_score
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        if n_clusters < 2 or len(feature_matrix) < 2:
            return {'error': 'Not enough clusters or data points'}
        
        # Silhouette score (-1 to 1, higher is better)
        silhouette = silhouette_score(feature_matrix, labels)
        
        # Davies-Bouldin score (lower is better)
        db_score = davies_bouldin_score(feature_matrix, labels)
        
        # Cluster size distribution
        unique_labels, counts = np.unique(labels[labels >= 0], return_counts=True)
        
        return {
            'n_clusters': n_clusters,
            'silhouette_score': round(float(silhouette), 3),
            'davies_bouldin_score': round(float(db_score), 3),
            'avg_cluster_size': round(float(np.mean(counts)), 2),
            'max_cluster_size': int(np.max(counts)),
            'min_cluster_size': int(np.min(counts)),
            'quality_rating': _get_quality_rating(silhouette)
        }
        
    except ImportError:
        print("⚠️  scikit-learn not installed, skipping quality metrics")
        return {'error': 'scikit-learn required'}
    except Exception as e:
        print(f"⚠️  Failed to analyze cluster quality: {e}")
        return {'error': str(e)}


def _get_quality_rating(silhouette_score: float) -> str:
    """Convert silhouette score to quality rating"""
    if silhouette_score >= 0.7:
        return "EXCELLENT"
    elif silhouette_score >= 0.5:
        return "GOOD"
    elif silhouette_score >= 0.3:
        return "FAIR"
    else:
        return "POOR"


def get_cluster_statistics(neo4j_conn) -> Dict:
    """
    Get overall clustering statistics from Neo4j
    
    Returns:
        Dict with statistics by algorithm
    """
    
    query = """
    MATCH (c:Cluster)
    OPTIONAL MATCH (c)<-[:BELONGS_TO]-(w:Wallet)
    
    WITH c.algorithm as algorithm,
         count(DISTINCT c) as cluster_count,
         count(DISTINCT w) as total_wallets,
         avg(c.avg_risk_score) as avg_cluster_risk
    
    RETURN algorithm,
           cluster_count,
           total_wallets,
           avg_cluster_risk
    ORDER BY cluster_count DESC
    """
    
    try:
        result = neo4j_conn.execute_query(query)
        
        stats_by_algorithm = {}
        
        for record in result:
            algo = record.get('algorithm', 'unknown')
            stats_by_algorithm[algo] = {
                'cluster_count': record['cluster_count'],
                'total_wallets': record.get('total_wallets', 0),
                'avg_cluster_risk': round(record.get('avg_cluster_risk', 0), 2)
            }
        
        # Overall stats
        total_query = """
        MATCH (c:Cluster)
        RETURN count(c) as total_clusters
        """
        
        total_result = neo4j_conn.execute_query(total_query)
        total_clusters = total_result[0]['total_clusters'] if total_result else 0
        
        return {
            'total_clusters': total_clusters,
            'by_algorithm': stats_by_algorithm
        }
        
    except Exception as e:
        print(f"⚠️  Failed to get cluster statistics: {e}")
        return {}


# Test function
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    
    from modules.graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Cluster Analyzer")
    print("="*60 + "\n")
    
    try:
        with Neo4jConnection() as conn:
            # Test 1: Get overall statistics
            print("Test 1: Cluster Statistics")
            stats = get_cluster_statistics(conn)
            print(f"Stats: {stats}")
            
            # Test 2: Inter-cluster transactions
            print("\nTest 2: Inter-Cluster Transactions")
            inter_txs = find_inter_cluster_transactions(conn, min_transactions=1)
            print(f"Found {len(inter_txs)} inter-cluster flows")
            
            print("\n✅ All cluster analyzer tests completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
