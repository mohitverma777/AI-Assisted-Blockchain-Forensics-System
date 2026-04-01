"""
Community Detection
Graph-based clustering using Neo4j and network algorithms
Authors: Krusha (Primary), Mohit (Integration)
"""

from typing import Dict, List, Tuple


def detect_communities_label_propagation(neo4j_conn, write_property: str = 'community_lp') -> Dict:
    """
    Label Propagation Algorithm - Fast community detection
    Each node takes the label that most of its neighbors have
    
    Args:
        neo4j_conn: Neo4jConnection instance
        write_property: Property name to store community ID
        
    Returns:
        Dict with community statistics
    """
    
    print(f"\n🔍 Running Label Propagation community detection...")
    
    try:
        # Check if we have graph relationships
        count_query = """
        MATCH (w1:Wallet)-[:SENT|RECEIVED_BY]-(t:Transaction)-[:SENT|RECEIVED_BY]-(w2:Wallet)
        RETURN count(DISTINCT w1) as wallet_count
        """
        
        count_result = neo4j_conn.execute_query(count_query)
        wallet_count = count_result[0]['wallet_count'] if count_result else 0
        
        if wallet_count < 2:
            print("⚠️  Not enough connected wallets for community detection")
            return {'communities': 0, 'wallets': 0}
        
        # Simple label propagation algorithm (native implementation)
        # Assign each wallet to its own community initially
        init_query = """
        MATCH (w:Wallet)
        SET w.community_lp = id(w)
        RETURN count(w) as initialized
        """
        
        neo4j_conn.execute_query(init_query)
        
        # Iterate: each wallet adopts most common community among neighbors
        iterations = 5
        for i in range(iterations):
            update_query = """
            MATCH (w:Wallet)-[:SENT|RECEIVED_BY*1..2]-(neighbor:Wallet)
            WHERE neighbor.community_lp IS NOT NULL
            WITH w, neighbor.community_lp as neighbor_community, count(*) as frequency
            ORDER BY frequency DESC
            WITH w, collect(neighbor_community)[0] as most_common_community
            SET w.community_lp = most_common_community
            RETURN count(w) as updated
            """
            
            result = neo4j_conn.execute_query(update_query)
            updated = result[0]['updated'] if result else 0
            print(f"   Iteration {i+1}: Updated {updated} wallets")
        
        # Get statistics
        stats_query = """
        MATCH (w:Wallet)
        WHERE w.community_lp IS NOT NULL
        WITH w.community_lp as community_id, count(w) as size
        RETURN count(community_id) as num_communities,
               sum(size) as total_wallets,
               avg(size) as avg_size,
               max(size) as max_size
        """
        
        stats = neo4j_conn.execute_query(stats_query)
        
        if stats:
            result = {
                'algorithm': 'label_propagation',
                'communities': stats[0]['num_communities'],
                'wallets': stats[0]['total_wallets'],
                'avg_size': round(stats[0]['avg_size'], 2),
                'max_size': stats[0]['max_size']
            }
            
            print(f"✅ Label Propagation complete:")
            print(f"   Communities: {result['communities']}")
            print(f"   Wallets: {result['wallets']}")
            print(f"   Avg size: {result['avg_size']}")
            
            return result
        
        return {'communities': 0, 'wallets': 0}
        
    except Exception as e:
        print(f"❌ Label propagation failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def find_connected_components(neo4j_conn) -> List[List[str]]:
    """
    Find weakly connected components in the wallet graph
    (Basic clustering: groups of wallets with any path between them)
    
    Returns:
        List of wallet address lists (one per component)
    """
    
    print(f"\n🔍 Finding connected components...")
    
    try:
        # Find all connected components
        query = """
        MATCH (start:Wallet)
        WHERE NOT (start)-[:COMPONENT_OF]->()
        
        // Find all wallets reachable from start
        CALL {
            WITH start
            MATCH path = (start)-[:SENT|RECEIVED_BY*1..5]-(connected:Wallet)
            RETURN DISTINCT connected
            UNION
            WITH start
            RETURN start as connected
        }
        
        WITH start, collect(DISTINCT connected.address) as component_wallets
        WHERE size(component_wallets) > 1
        
        RETURN component_wallets
        LIMIT 100
        """
        
        results = neo4j_conn.execute_query(query)
        
        components = []
        for record in results:
            wallet_list = record.get('component_wallets', [])
            if len(wallet_list) >= 2:
                components.append(wallet_list)
        
        # Sort by size
        components.sort(key=len, reverse=True)
        
        print(f"✅ Found {len(components)} connected components")
        for i, comp in enumerate(components[:5], 1):
            print(f"   Component {i}: {len(comp)} wallets")
        
        return components
        
    except Exception as e:
        print(f"❌ Connected components detection failed: {e}")
        return []


def detect_communities_louvain(neo4j_conn) -> Dict:
    """
    Louvain Method for community detection
    
    NOTE: Requires Neo4j Graph Data Science (GDS) library
    If not available, falls back to label propagation
    
    Returns:
        Community statistics
    """
    
    print(f"\n🔍 Attempting Louvain community detection...")
    
    try:
        # Check if GDS is available
        version_query = "CALL gds.version() YIELD version RETURN version"
        
        try:
            version_result = neo4j_conn.execute_query(version_query)
            gds_version = version_result[0]['version']
            print(f"   Neo4j GDS version: {gds_version}")
        except:
            print("⚠️  Neo4j GDS not available, falling back to Label Propagation")
            return detect_communities_label_propagation(neo4j_conn)
        
        # Create graph projection
        project_query = """
        CALL gds.graph.project(
            'wallet-community-graph',
            'Wallet',
            {
                TRANSACTED_WITH: {
                    type: 'SENT',
                    orientation: 'UNDIRECTED'
                }
            }
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
        """
        
        # Check if graph exists, drop if needed
        try:
            drop_query = "CALL gds.graph.drop('wallet-community-graph') YIELD graphName"
            neo4j_conn.execute_query(drop_query)
        except:
            pass
        
        proj_result = neo4j_conn.execute_query(project_query)
        
        # Run Louvain
        louvain_query = """
        CALL gds.louvain.write('wallet-community-graph', {
            writeProperty: 'community_louvain'
        })
        YIELD communityCount, modularity
        RETURN communityCount, modularity
        """
        
        louvain_result = neo4j_conn.execute_query(louvain_query)
        
        if louvain_result:
            result = {
                'algorithm': 'louvain',
                'communities': louvain_result[0]['communityCount'],
                'modularity': round(louvain_result[0]['modularity'], 4)
            }
            
            print(f"✅ Louvain complete:")
            print(f"   Communities: {result['communities']}")
            print(f"   Modularity: {result['modularity']}")
            
            return result
        
        return {'communities': 0}
        
    except Exception as e:
        print(f"⚠️  Louvain failed: {e}")
        print("   Falling back to Label Propagation...")
        return detect_communities_label_propagation(neo4j_conn)


# Test function
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    
    from modules.graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Community Detection")
    print("="*60 + "\n")
    
    try:
        with Neo4jConnection() as conn:
            # Test 1: Label Propagation
            print("Test 1: Label Propagation")
            lp_result = detect_communities_label_propagation(conn)
            
            # Test 2: Connected Components
            print("\nTest 2: Connected Components")
            components = find_connected_components(conn)
            
            # Test 3: Louvain (may fall back to LP)
            print("\nTest 3: Louvain Method")
            louvain_result = detect_communities_louvain(conn)
            
            print("\n✅ All community detection tests completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
