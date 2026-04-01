"""
Behavioral Clustering
K-Means and DBSCAN clustering based on wallet behavioral features
Authors: Mohit (Primary), Mohit (Integration)
"""

from typing import Dict, List, Tuple
import numpy as np
from collections import defaultdict


def extract_behavioral_features(neo4j_conn, wallet_addresses: List[str] = None) -> Tuple[List[str], np.ndarray]:
    """
    Extract behavioral features from wallets for clustering
    
    Features:
    - Transaction velocity (TX per day)
    - Average transaction amount
    - Balance volatility
    - Transaction frequency patterns
    - Round number ratio
    
    Args:
        neo4j_conn: Neo4jConnection instance
        wallet_addresses: Optional list of specific wallets (None = all wallets)
        
    Returns:
        Tuple of (wallet_addresses, feature_matrix)
    """
    
    print(f"\n📊 Extracting behavioral features...")
    
    # Query for wallet features
    if wallet_addresses:
        where_clause = "WHERE w.address IN $addresses"
        params = {"addresses": wallet_addresses}
    else:
        where_clause = "WHERE w.total_transactions > 5"  # Only active wallets
        params = {}
    
    query = f"""
    MATCH (w:Wallet)
    {where_clause}
    OPTIONAL MATCH (w)-[r:SENT|RECEIVED_BY]-(t:Transaction)
    WITH w, 
         count(DISTINCT t) as tx_count,
         collect(t.value) as tx_values,
         collect(t.timestamp) as tx_timestamps
    WHERE tx_count > 0
    RETURN w.address as address,
           w.balance as balance,
           w.total_transactions as total_txs,
           tx_count,
           tx_values,
           tx_timestamps
    LIMIT 1000
    """
    
    try:
        results = neo4j_conn.execute_query(query, params)
        
        if not results:
            print("⚠️  No wallets found for feature extraction")
            return [], np.array([])
        
        addresses = []
        features = []
        
        for record in results:
            addr = record['address']
            addresses.append(addr)
            
            # Extract timestamp values
            tx_times = []
            for ts in record.get('tx_timestamps', []):
                if hasattr(ts, 'timestamp'):
                    tx_times.append(ts.timestamp())
                elif isinstance(ts, (int, float)):
                    tx_times.append(float(ts))
            
            # Calculate features
            feature_vec = _calculate_features(
                balance=record.get('balance', 0),
                total_txs=record.get('total_txs', 0),
                tx_values=record.get('tx_values', []),
                tx_timestamps=tx_times
            )
            
            features.append(feature_vec)
        
        feature_matrix = np.array(features)
        
        print(f"✅ Extracted features for {len(addresses)} wallets")
        print(f"   Feature dimensions: {feature_matrix.shape[1]}")
        
        return addresses, feature_matrix
        
    except Exception as e:
        print(f"❌ Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return [], np.array([])


def _calculate_features(balance: float, total_txs: int, tx_values: List, tx_timestamps: List) -> List[float]:
    """Calculate behavioral feature vector"""
    
    # Feature 1: Log balance (avoid zero)
    log_balance = np.log1p(balance) if balance > 0 else 0
    
    # Feature 2: Transaction count (log scale)
    log_tx_count = np.log1p(total_txs)
    
    # Feature 3: Average transaction value
    avg_tx_value = np.mean([abs(v) for v in tx_values if v != 0]) if tx_values else 0
    log_avg_value = np.log1p(avg_tx_value)
    
    # Feature 4: Transaction value std (volatility)
    tx_volatility = np.std([abs(v) for v in tx_values if v != 0]) if len(tx_values) > 1 else 0
    log_volatility = np.log1p(tx_volatility)
    
    # Feature 5: Transaction velocity (if we have timestamps)
    if len(tx_timestamps) >= 2:
        sorted_times = sorted([t for t in tx_timestamps if t > 0])
        if len(sorted_times) >= 2:
            time_span_days = (sorted_times[-1] - sorted_times[0]) / 86400
            tx_per_day = total_txs / max(1, time_span_days)
        else:
            tx_per_day = 0
    else:
        tx_per_day = 0
    
    # Feature 6: Round number ratio
    round_count = sum(1 for v in tx_values if _is_round_number(v))
    round_ratio = round_count / max(1, len(tx_values))
    
    return [
        log_balance,
        log_tx_count,
        log_avg_value,
        log_volatility,
        min(tx_per_day, 100),  # Cap at 100
        round_ratio
    ]


def _is_round_number(value: float, threshold: float = 0.01) -> bool:
    """Check if value is a round number"""
    if value == 0:
        return False
    
    abs_val = abs(value)
    # Check if it's close to 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, etc.
    round_values = [0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]
    
    for rv in round_values:
        if abs(abs_val - rv) / rv < threshold:
            return True
    
    return False


def cluster_wallets_kmeans(feature_matrix: np.ndarray, n_clusters: int = 5) -> np.ndarray:
    """
    K-Means clustering on behavioral features
    
    Args:
        feature_matrix: Feature matrix (n_wallets, n_features)
        n_clusters: Number of clusters
        
    Returns:
        Cluster labels array
    """
    
    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        print(f"\n🎯 Running K-Means clustering (k={n_clusters})...")
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_matrix)
        
        # K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features_scaled)
        
        # Print cluster sizes
        unique, counts = np.unique(labels, return_counts=True)
        print(f"✅ K-Means complete:")
        for cluster_id, count in zip(unique, counts):
            print(f"   Cluster {cluster_id}: {count} wallets")
        
        return labels
        
    except ImportError:
        print("❌ scikit-learn not installed. Run: pip install scikit-learn")
        return np.array([])
    except Exception as e:
        print(f"❌ K-Means clustering failed: {e}")
        return np.array([])


def cluster_wallets_dbscan(feature_matrix: np.ndarray, eps: float = 0.5, min_samples: int = 3) -> np.ndarray:
    """
    DBSCAN clustering (density-based, finds arbitrary shapes)
    
    Args:
        feature_matrix: Feature matrix
        eps: Maximum distance between samples
        min_samples: Minimum samples in neighborhood
        
    Returns:
        Cluster labels array (-1 = noise/outliers)
    """
    
    try:
        from sklearn.cluster import DBSCAN
        from sklearn.preprocessing import StandardScaler
        
        print(f"\n🎯 Running DBSCAN clustering (eps={eps}, min_samples={min_samples})...")
        
        # Standardize
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_matrix)
        
        # DBSCAN
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(features_scaled)
        
        # Print results
        unique, counts = np.unique(labels, return_counts=True)
        n_clusters = len(unique[unique >= 0])
        n_noise = counts[unique == -1][0] if -1 in unique else 0
        
        print(f"✅ DBSCAN complete:")
        print(f"   Clusters found: {n_clusters}")
        print(f"   Noise points: {n_noise}")
        
        for cluster_id, count in zip(unique[unique >= 0], counts[unique >= 0]):
            print(f"   Cluster {cluster_id}: {count} wallets")
        
        return labels
        
    except ImportError:
        print("❌ scikit-learn not installed. Run: pip install scikit-learn")
        return np.array([])
    except Exception as e:
        print(f"❌ DBSCAN clustering failed: {e}")
        return np.array([])


# Test function
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    
    from modules.graph import Neo4jConnection
    
    print("\n" + "="*60)
    print("🧪 Testing Behavioral Clustering")
    print("="*60 + "\n")
    
    try:
        with Neo4jConnection() as conn:
            # Extract features
            addresses, features = extract_behavioral_features(conn)
            
            if len(features) > 0:
                print(f"\nFeature matrix shape: {features.shape}")
                print(f"Sample features (first wallet): {features[0]}")
                
                # Test K-Means
                if len(features) >= 5:
                    labels_kmeans = cluster_wallets_kmeans(features, n_clusters=3)
                    
                    # Test DBSCAN
                    labels_dbscan = cluster_wallets_dbscan(features, eps=0.8, min_samples=2)
                
                print("\n✅ All behavioral clustering tests completed!")
            else:
                print("⚠️  No features extracted - add more wallets to database first")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
