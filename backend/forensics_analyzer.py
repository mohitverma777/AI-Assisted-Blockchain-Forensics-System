"""
Unified Forensics Analyzer
Main API that combines blockchain fetching, Neo4j graph, and risk scoring
Authors: Mohit (Integration Lead), Team

This is the primary entry point for complete wallet forensic analysis.
"""

import sys
import os

# Add backend src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from typing import Dict, Optional
from datetime import datetime


def analyze_wallet_complete(wallet_address: str, blockchain: str = "auto", save_to_json: bool = False) -> Dict:
    """
    Complete end-to-end forensic analysis of a wallet
    
    This function orchestrates all modules:
    1. Fetches blockchain data (Ethereum or Bitcoin)
    2. Stores data in Neo4j graph database
    3. Calculates graph metrics
    4. Runs risk scoring analysis (10 factors)
    5. Enriches Neo4j with risk scores
    
    Args:
        wallet_address: Wallet address to analyze
        blockchain: "auto", "ethereum", or "bitcoin"
        save_to_json: Also save raw data to JSON file
        
    Returns:
        Complete analysis report with blockchain data, graph metrics, and risk analysis
    """
    
    print(f"\n{'='*70}")
    print(f"🔍 BLOCKCHAIN FORENSIC ANALYSIS - COMPLETE SYSTEM")
    print(f"{'='*70}")
    print(f"Wallet: {wallet_address}")
    print(f"Blockchain: {blockchain.upper()}")
    print(f"{'='*70}\n")
    
    try:
        # STEP 1: Fetch blockchain data and store in Neo4j
        print("📡 STEP 1/5: Fetching blockchain data...")
        from modules.blockchain.unified_blockchain_api import BlockchainForensics
        
        fetcher = BlockchainForensics()
        blockchain_data = fetcher.analyze_wallet(
            wallet_address, 
            blockchain, 
            save_to_neo4j=True,
            save_to_json=save_to_json
        )
        
        print(f"✅ Fetched {len(blockchain_data.get('normal_transactions', blockchain_data.get('transactions', [])))} transactions")
        
        # STEP 2: Calculate graph metrics from Neo4j
        print("\n📊 STEP 2/5: Calculating graph metrics...")
        from modules.graph import Neo4jConnection
        from modules.integration.graph_analyzer import calculate_graph_metrics, calculate_dormancy_metrics
        
        with Neo4jConnection() as neo4j_conn:
            graph_metrics = calculate_graph_metrics(neo4j_conn, wallet_address)
            dormancy_metrics = calculate_dormancy_metrics(neo4j_conn, wallet_address)
            
        print(f"✅ Cluster size: {graph_metrics['cluster_size']}, Avg degree: {graph_metrics['avg_degree']}")
        
        # STEP 3: Transform data to risk engine format
        print("\n🔄 STEP 3/5: Transforming data for risk analysis...")
        from modules.integration.data_transformer import blockchain_to_risk_format
        
        risk_input = blockchain_to_risk_format(blockchain_data)
        risk_input.update(graph_metrics)
        risk_input.update(dormancy_metrics)
        
        print(f"✅ Data prepared for risk scoring")
        
        # STEP 4: Calculate risk score
        print("\n🎯 STEP 4/5: Running risk analysis (10 factors)...")
        from modules.risk.risk_engine import risk_engine
        
        risk_result = risk_engine(risk_input)
        
        print(f"✅ Risk Score: {risk_result['overall_risk']}/100 ({risk_result['risk_band']}) {risk_result['risk_color']}")
        
        # STEP 5: Enrich Neo4j with risk data
        print("\n💾 STEP 5/5: Enriching Neo4j with risk scores...")
        from modules.integration.graph_enricher import enrich_wallet_with_risk
        
        with Neo4jConnection() as neo4j_conn:
            success = enrich_wallet_with_risk(neo4j_conn, wallet_address, risk_result)
        
        if success:
            print(f"✅ Risk data added to Neo4j graph")
        
        # Compile complete report
        complete_report = {
            'wallet_address': wallet_address,
            'blockchain': blockchain_data['blockchain'],
            'timestamp': datetime.now().isoformat(),
            'blockchain_data': {
                'balance': blockchain_data.get('balance', {}),
                'transaction_count': len(blockchain_data.get('normal_transactions', blockchain_data.get('transactions', [])))
            },
            'graph_metrics': {
                **graph_metrics,
                **dormancy_metrics
            },
            'risk_analysis': risk_result
        }
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"{'='*70}")
        print(f"\n📊 Summary:")
        print(f"   Balance: {blockchain_data.get('balance', {})}")
        print(f"   Transactions: {complete_report['blockchain_data']['transaction_count']}")
        print(f"   Connected Wallets: {graph_metrics['cluster_size']}")
        print(f"\n🎯 Risk Assessment:")
        print(f"   Overall Risk: {risk_result['overall_risk']}/100")
        print(f"   Risk Level: {risk_result['risk_band']} {risk_result['risk_color']}")
        print(f"   Top Factors:")
        for factor in risk_result['top_factors'][:3]:
            print(f"      • {factor}")
        
        if risk_result.get('investigation_leads'):
            print(f"\n🔍 Investigation Leads:")
            for lead in risk_result['investigation_leads']:
                print(f"      {lead}")
        
        print(f"\n💡 View in Neo4j Browser:")
        print(f"   http://localhost:7474")
        print(f"   Query: MATCH (w:Wallet {{address: '{wallet_address}'}}) RETURN w")
        print(f"\n{'='*70}\n")
        
        return complete_report
        
    except ImportError as e:
        print(f"\n❌ Module not found: {e}")
        print(f"   Make sure all dependencies are installed: pip install -r requirements.txt")
        raise
        
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        print(f"   Make sure Neo4j is running: docker-compose up -d")
        raise
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def analyze_multiple_wallets(wallet_addresses: list, blockchain: str = "auto") -> list:
    """
    Analyze multiple wallets in batch
    
    Args:
        wallet_addresses: List of wallet addresses
        blockchain: Blockchain type
        
    Returns:
        List of analysis reports
    """
    
    print(f"\n{'='*70}")
    print(f"🔄 BATCH ANALYSIS: {len(wallet_addresses)} wallets")
    print(f"{'='*70}\n")
    
    results = []
    
    for i, wallet in enumerate(wallet_addresses, 1):
        print(f"\n[{i}/{len(wallet_addresses)}] Analyzing: {wallet[:20]}...")
        try:
            result = analyze_wallet_complete(wallet, blockchain)
            results.append(result)
        except Exception as e:
            print(f"⚠️  Skipped due to error: {e}")
            results.append({
                'wallet_address': wallet,
                'error': str(e),
                'status': 'failed'
            })
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 BATCH ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"Total wallets: {len(wallet_addresses)}")
    print(f"Successful: {sum(1 for r in results if 'error' not in r)}")
    print(f"Failed: {sum(1 for r in results if 'error' in r)}")
    
    # Risk distribution
    successful = [r for r in results if 'error' not in r]
    if successful:
        risk_levels = {}
        for r in successful:
            level = r.get('risk_analysis', {}).get('risk_band', 'UNKNOWN')
            risk_levels[level] = risk_levels.get(level, 0) + 1
        
        print(f"\n🎯 Risk Distribution:")
        for level, count in sorted(risk_levels.items()):
            print(f"   {level}: {count} wallets")
    
    print(f"{'='*70}\n")
    
    return results


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete Blockchain Forensic Analysis')
    parser.add_argument('wallet', help='Wallet address to analyze')
    parser.add_argument('--blockchain', '-b', default='auto', choices=['auto', 'ethereum', 'bitcoin'],
                       help='Blockchain type (default: auto-detect)')
    parser.add_argument('--json', action='store_true', help='Also save to JSON file')
    
    args = parser.parse_args()
    
    try:
        result = analyze_wallet_complete(args.wallet, args.blockchain, args.json)
        print("\n✅ Analysis saved to Neo4j database!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
