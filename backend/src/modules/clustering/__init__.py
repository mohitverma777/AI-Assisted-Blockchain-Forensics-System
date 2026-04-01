"""
Clustering Module - Wallet Grouping and Community Detection
Identifies groups of wallets that likely belong to same entity or exhibit similar patterns
"""

from .heuristic_clustering import (
    cluster_by_common_inputs,
    find_change_addresses,
    detect_co_spending_patterns
)

from .behavioral_clustering import (
    extract_behavioral_features,
    cluster_wallets_kmeans,
    cluster_wallets_dbscan
)

from .community_detection import (
    detect_communities_louvain,
    detect_communities_label_propagation,
    find_connected_components
)

from .cluster_analyzer import (
    analyze_cluster_quality,
    aggregate_cluster_risk,
    find_inter_cluster_transactions,
    get_cluster_statistics
)

from .neo4j_clustering import (
    create_cluster_node,
    assign_wallets_to_cluster,
    get_wallet_clusters,
    update_cluster_statistics
)

__all__ = [
    # Heuristic
    'cluster_by_common_inputs',
    'find_change_addresses',
    'detect_co_spending_patterns',
    # Behavioral
    'extract_behavioral_features',
    'cluster_wallets_kmeans',
    'cluster_wallets_dbscan',
    # Community Detection
    'detect_communities_louvain',
    'detect_communities_label_propagation',
    'find_connected_components',
    # Analysis
    'analyze_cluster_quality',
    'aggregate_cluster_risk',
    'find_inter_cluster_transactions',
    'get_cluster_statistics',
    # Neo4j
    'create_cluster_node',
    'assign_wallets_to_cluster',
    'get_wallet_clusters',
    'update_cluster_statistics'
]
