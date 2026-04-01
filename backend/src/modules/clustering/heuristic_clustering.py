"""
Heuristic Clustering
Transaction-based clustering using blockchain heuristics
Authors: Krusha (Primary), Mohit (Integration)
"""

from typing import Dict, List, Set, Tuple
from collections import defaultdict


def cluster_by_common_inputs(neo4j_conn, min_shared_txs: int = 2) -> List[Set[str]]:
    """
    Common Input Heuristic: Wallets appearing as inputs in the same transaction
    likely belong to the same entity
    
    Args:
        neo4j_conn: Neo4jConnection instance
        min_shared_txs: Minimum number of shared transactions to cluster
        
    Returns:
        List of wallet address sets (clusters)
    """
    
    print(f"\n🔍 Running Common Input Heuristic Clustering...")
    
    # Find wallets that co-spend (both send to same transaction)
    query = """
    MATCH (w1:Wallet)-[:SENT]->(t:Transaction)<-[:SENT]-(w2:Wallet)
    WHERE w1.address < w2.address
    WITH w1.address as addr1, w2.address as addr2, count(t) as shared_txs
    WHERE shared_txs >= $min_shared
    RETURN addr1, addr2, shared_txs
    ORDER BY shared_txs DESC
    """
    
    try:
        results = neo4j_conn.execute_query(query, {"min_shared": min_shared_txs})
        
        if not results:
            print("⚠️  No co-spending patterns found")
            return []
        
        # Build clusters using Union-Find
        clusters = _build_clusters_union_find(results)
        
        print(f"✅ Found {len(clusters)} clusters from common inputs")
        for i, cluster in enumerate(clusters[:5], 1):
            print(f"   Cluster {i}: {len(cluster)} wallets")
        
        return clusters
        
    except Exception as e:
        print(f"❌ Common input clustering failed: {e}")
        return []


def detect_co_spending_patterns(neo4j_conn, wallet_address: str) -> List[Dict]:
    """
    Find wallets that frequently co-spend with the given wallet
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Target wallet address
        
    Returns:
        List of co-spending wallet info
    """
    
    query = """
    MATCH (w1:Wallet {address: $address})-[:SENT]->(t:Transaction)<-[:SENT]-(w2:Wallet)
    WHERE w1 <> w2
    WITH w2, count(t) as shared_txs, collect(t.hash)[..5] as sample_txs
    WHERE shared_txs >= 2
    RETURN w2.address as wallet, 
           w2.risk_score as risk_score,
           shared_txs as co_spending_count,
           sample_txs
    ORDER BY shared_txs DESC
    LIMIT 20
    """
    
    try:
        results = neo4j_conn.execute_query(query, {"address": wallet_address})
        
        co_spenders = []
        for record in results:
            co_spenders.append({
                'wallet': record['wallet'],
                'risk_score': record.get('risk_score', 0),
                'co_spending_count': record['co_spending_count'],
                'sample_transactions': record.get('sample_txs', []),
                'confidence': min(0.95, 0.5 + (record['co_spending_count'] * 0.1))
            })
        
        return co_spenders
        
    except Exception as e:
        print(f"⚠️  Co-spending detection failed: {e}")
        return []


def find_change_addresses(neo4j_conn, wallet_address: str) -> List[str]:
    """
    Identify likely change addresses (one-time outputs that go back to sender)
    
    Change address indicators:
    - Used only once (received once, sent once)
    - Received from target wallet
    - Short time between receive and send
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_address: Source wallet address
        
    Returns:
        List of likely change addresses
    """
    
    query = """
    // Find wallets that received from target
    MATCH (source:Wallet {address: $address})-[:SENT]->(t1:Transaction)-[:RECEIVED_BY]->(candidate:Wallet)
    
    // Count their total transactions
    MATCH (candidate)-[r]-(t:Transaction)
    WITH candidate, count(DISTINCT t) as total_txs, t1
    WHERE total_txs <= 2  // One-time or minimal use
    
    // Check if they sent everything out
    OPTIONAL MATCH (candidate)-[:SENT]->(t2:Transaction)
    WHERE t2.timestamp > t1.timestamp
    
    RETURN candidate.address as change_address,
           candidate.balance as remaining_balance,
           total_txs
    """
    
    try:
        results = neo4j_conn.execute_query(query, {"address": wallet_address})
        
        change_addresses = []
        for record in results:
            # Change address typically has near-zero balance
            if record.get('remaining_balance', 0) < 0.01:
                change_addresses.append(record['change_address'])
        
        if change_addresses:
            print(f"✅ Found {len(change_addresses)} likely change addresses")
        
        return change_addresses
        
    except Exception as e:
        print(f"⚠️  Change address detection failed: {e}")
        return []


def _build_clusters_union_find(pair_results: List[Dict]) -> List[Set[str]]:
    """
    Build clusters from pairwise relationships using Union-Find algorithm
    
    Args:
        pair_results: List of dicts with 'addr1', 'addr2' keys
        
    Returns:
        List of wallet address sets
    """
    
    parent = {}
    
    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])  # Path compression
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Build union-find structure
    for record in pair_results:
        addr1 = record['addr1']
        addr2 = record['addr2']
        union(addr1, addr2)
    
    # Group by root parent
    clusters_dict = defaultdict(set)
    for addr in parent:
        root = find(addr)
        clusters_dict[root].add(addr)
        clusters_dict[root].add(root)
    
    # Convert to list of sets
    clusters = [cluster for cluster in clusters_dict.values() if len(cluster) >= 2]
    
    # Sort by size
    clusters.sort(key=len, reverse=True)
    
    return clusters


# Test function
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    
    from modules.graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Heuristic Clustering")
    print("="*60 + "\n")
    
    try:
        with Neo4jConnection() as conn:
            # Test 1: Common inputs
            print("Test 1: Common Input Clustering")
            clusters = cluster_by_common_inputs(conn, min_shared_txs=2)
            
            if clusters:
                print(f"\nFound {len(clusters)} clusters:")
                for i, cluster in enumerate(clusters[:3], 1):
                    print(f"  Cluster {i}: {list(cluster)[:3]}... ({len(cluster)} total)")
            
            # Test 2: Co-spending (if we have a wallet)
            print("\n\nTest 2: Co-spending Detection")
            test_wallet = "0xF977814e90dA44bFA03b6295A0616a897441aceC"
            co_spenders = detect_co_spending_patterns(conn, test_wallet)
            
            if co_spenders:
                print(f"Found {len(co_spenders)} co-spenders:")
                for cs in co_spenders[:3]:
                    print(f"  {cs['wallet'][:20]}... - {cs['co_spending_count']} shared TXs")
            
            print("\n✅ All heuristic clustering tests completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
