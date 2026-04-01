"""
Neo4j Clustering Integration
Manages Cluster nodes and wallet-cluster relationships in Neo4j
Authors: Mohit (Integration Lead), Krusha (Graph Support)
"""

from typing import Dict, List, Optional
from datetime import datetime


def create_cluster_node(neo4j_conn, cluster_data: Dict) -> str:
    """
    Create a Cluster node in Neo4j
    
    Args:
        neo4j_conn: Neo4jConnection instance
        cluster_data: Dict with cluster properties
            - algorithm: "heuristic"|"behavioral"|"community"
            - cluster_type: Optional description
            - wallet_addresses: List of wallet addresses
            
    Returns:
        cluster_id (string)
    """
    
    algorithm = cluster_data.get('algorithm', 'unknown')
    cluster_type = cluster_data.get('cluster_type', 'general')
    wallet_addresses = cluster_data.get('wallet_addresses', [])
    
    # Generate cluster ID
    cluster_id = f"{algorithm}_{cluster_type}_{len(wallet_addresses)}_{datetime.now().timestamp()}"
    
    query = """
    CREATE (c:Cluster {
        cluster_id: $cluster_id,
        algorithm: $algorithm,
        cluster_type: $cluster_type,
        size: $size,
        creation_date: datetime(),
        avg_risk_score: 0.0,
        total_balance: 0.0
    })
    RETURN c.cluster_id as cluster_id
    """
    
    try:
        params = {
            'cluster_id': cluster_id,
            'algorithm': algorithm,
            'cluster_type': cluster_type,
            'size': len(wallet_addresses)
        }
        
        result = neo4j_conn.execute_query(query, params)
        
        if result:
            print(f"✅ Created cluster: {cluster_id}")
            return cluster_id
        
        return ""
        
    except Exception as e:
        print(f"❌ Failed to create cluster: {e}")
        return ""


def assign_wallets_to_cluster(neo4j_conn, wallet_addresses: List[str], cluster_id: str, confidence: float = 1.0) -> int:
    """
    Assign wallets to a cluster
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_addresses: List of wallet addresses
        cluster_id: Cluster ID
        confidence: Confidence score (0.0-1.0)
        
    Returns:
        Number of wallets assigned
    """
    
    query = """
    UNWIND $addresses as addr
    MATCH (w:Wallet {address: addr})
    MATCH (c:Cluster {cluster_id: $cluster_id})
    MERGE (w)-[r:BELONGS_TO]->(c)
    SET r.confidence = $confidence,
        r.assigned_date = datetime()
    RETURN count(r) as assigned_count
    """
    
    try:
        params = {
            'addresses': wallet_addresses,
            'cluster_id': cluster_id,
            'confidence': confidence
        }
        
        result = neo4j_conn.execute_query(query, params)
        
        if result:
            count = result[0]['assigned_count']
            print(f"✅ Assigned {count} wallets to cluster {cluster_id}")
            return count
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to assign wallets: {e}")
        return 0


def update_cluster_statistics(neo4j_conn, cluster_id: str) -> Dict:
    """
    Calculate and update cluster statistics
    
    Args:
        neo4j_conn: Neo4jConnection instance
        cluster_id: Cluster ID
        
    Returns:
        Dict with updated statistics
    """
    
    query = """
    MATCH (c:Cluster {cluster_id: $cluster_id})<-[:BELONGS_TO]-(w:Wallet)
    WITH c,
         count(w) as size,
         avg(w.risk_score) as avg_risk,
         sum(w.balance) as total_balance,
         max(w.risk_score) as max_risk,
         collect(w.risk_level) as risk_levels
    
    SET c.size = size,
        c.avg_risk_score = coalesce(avg_risk, 0.0),
        c.total_balance = coalesce(total_balance, 0.0),
        c.max_risk_score = coalesce(max_risk, 0.0),
        c.last_updated = datetime()
    
    RETURN c.cluster_id as cluster_id,
           size,
           avg_risk,
           total_balance,
           max_risk,
           risk_levels
    """
    
    try:
        result = neo4j_conn.execute_query(query, {'cluster_id': cluster_id})
        
        if result:
            stats = {
                'cluster_id': result[0]['cluster_id'],
                'size': result[0]['size'],
                'avg_risk_score': round(result[0].get('avg_risk', 0), 2),
                'total_balance': result[0].get('total_balance', 0),
                'max_risk_score': result[0].get('max_risk', 0)
            }
            
            print(f"✅ Updated statistics for cluster {cluster_id}")
            return stats
        
        return {}
        
    except Exception as e:
        print(f"❌ Failed to update statistics: {e}")
        return {}


def get_wallet_clusters(neo4j_conn, wallet_address: str) -> List[Dict]:
    """
    Get all clusters a wallet belongs to
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Wallet address
        
    Returns:
        List of cluster info dicts
    """
    
    query = """
    MATCH (w:Wallet {address: $address})-[r:BELONGS_TO]->(c:Cluster)
    RETURN c.cluster_id as cluster_id,
           c.algorithm as algorithm,
           c.cluster_type as cluster_type,
           c.size as size,
           c.avg_risk_score as avg_risk,
           r.confidence as confidence
    ORDER BY r.confidence DESC
    """
    
    try:
        result = neo4j_conn.execute_query(query, {'address': wallet_address})
        
        clusters = []
        for record in result:
            clusters.append({
                'cluster_id': record['cluster_id'],
                'algorithm': record.get('algorithm', 'unknown'),
                'cluster_type': record.get('cluster_type', 'general'),
                'size': record.get('size', 0),
                'avg_risk_score': record.get('avg_risk', 0),
                'confidence': record.get('confidence', 1.0)
            })
        
        return clusters
        
    except Exception as e:
        print(f"⚠️  Failed to get wallet clusters: {e}")
        return []


def get_cluster_wallets(neo4j_conn, cluster_id: str, limit: int = 100) -> List[Dict]:
    """
    Get all wallets in a cluster
    
    Args:
        neo4j_conn: Neo4jConnection instance
        cluster_id: Cluster ID
        limit: Maximum wallets to return
        
    Returns:
        List of wallet info dicts
    """
    
    query = """
    MATCH (c:Cluster {cluster_id: $cluster_id})<-[r:BELONGS_TO]-(w:Wallet)
    RETURN w.address as address,
           w.blockchain as blockchain,
           w.risk_score as risk_score,
           w.balance as balance,
           r.confidence as confidence
    ORDER BY w.risk_score DESC
    LIMIT $limit
    """
    
    try:
        result = neo4j_conn.execute_query(query, {'cluster_id': cluster_id, 'limit': limit})
        
        wallets = []
        for record in result:
            wallets.append({
                'address': record['address'],
                'blockchain': record.get('blockchain', 'unknown'),
                'risk_score': record.get('risk_score', 0),
                'balance': record.get('balance', 0),
                'confidence': record.get('confidence', 1.0)
            })
        
        return wallets
        
    except Exception as e:
        print(f"⚠️  Failed to get cluster wallets: {e}")
        return []


def query_high_risk_clusters(neo4j_conn, min_avg_risk: float = 60.0) -> List[Dict]:
    """
    Find high-risk clusters
    
    Args:
        neo4j_conn: Neo4jConnection instance
        min_avg_risk: Minimum average risk score
        
    Returns:
        List of high-risk cluster info
    """
    
    query = """
    MATCH (c:Cluster)
    WHERE c.avg_risk_score >= $min_avg_risk OR c.max_risk_score >= 80
    RETURN c.cluster_id as cluster_id,
           c.algorithm as algorithm,
           c.size as size,
           c.avg_risk_score as avg_risk,
           c.max_risk_score as max_risk,
           c.total_balance as total_balance
    ORDER BY c.avg_risk_score DESC
    LIMIT 20
    """
    
    try:
        result = neo4j_conn.execute_query(query, {'min_avg_risk': min_avg_risk})
        
        clusters = []
        for record in result:
            clusters.append({
                'cluster_id': record['cluster_id'],
                'algorithm': record.get('algorithm', 'unknown'),
                'size': record.get('size', 0),
                'avg_risk_score': round(record.get('avg_risk', 0), 2),
                'max_risk_score': record.get('max_risk', 0),
                'total_balance': record.get('total_balance', 0)
            })
        
        return clusters
        
    except Exception as e:
        print(f"⚠️  Failed to query high-risk clusters: {e}")
        return []


# Test function
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    
    from modules.graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Neo4j Clustering")
    print("="*60 + "\n")
    
    try:
        with Neo4jConnection() as conn:
            # Test 1: Create cluster
            print("Test 1: Create Cluster Node")
            cluster_data = {
                'algorithm': 'heuristic',
                'cluster_type': 'test',
                'wallet_addresses': ['0xTest1', '0xTest2', '0xTest3']
            }
            cluster_id = create_cluster_node(conn, cluster_data)
            
            if cluster_id:
                # Test 2: Assign wallets (note: wallets must exist)
                print("\nTest 2: Assign Wallets to Cluster")
                # This will only work if wallets exist in Neo4j
                
                # Test 3: Update statistics
                print("\nTest 3: Update Cluster Statistics")
                stats = update_cluster_statistics(conn, cluster_id)
                print(f"   Stats: {stats}")
                
                # Clean up test cluster
                cleanup_query = f"MATCH (c:Cluster {{cluster_id: '{cluster_id}'}}) DETACH DELETE c"
                conn.execute_query(cleanup_query)
                print(f"\n🧹 Cleaned up test cluster")
            
            print("\n✅ All Neo4j clustering tests completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
