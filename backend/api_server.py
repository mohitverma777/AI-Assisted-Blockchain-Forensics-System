"""
Flask REST API Server for Blockchain Forensics System
Connects backend modules with React frontend dashboard.
Enhanced with AI explanation and report generation.

Authors: Mohit (Primary), Krusha (Backup)
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sys
import os
import traceback
from datetime import datetime
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.blockchain import BlockchainForensics
from modules.ai.ai_explanation import AIExplanationGenerator, generate_ai_explanation, generate_graph_explanation
from modules.report.report_generator import ReportGenerator

# Try importing Neo4j and risk modules (graceful fallback if unavailable)
try:
    from modules.graph import Neo4jConnection
    HAS_NEO4J = True
except Exception:
    HAS_NEO4J = False
    print("[WARN] Neo4j module unavailable -- graph features disabled")

try:
    from modules.risk.risk_engine import risk_engine
    HAS_RISK_ENGINE = True
except Exception:
    HAS_RISK_ENGINE = False
    print("[WARN] Risk engine module unavailable -- using placeholder scores")


app = Flask(__name__)

# Configure CORS to allow frontend origin
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    },
    r"/health": {
        "origins": "*"
    }
})

# Initialize services
ai_generator = AIExplanationGenerator()
report_gen = ReportGenerator()


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Blockchain Forensics API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'modules': {
            'blockchain_fetcher': True,
            'neo4j_graph': HAS_NEO4J,
            'risk_engine': HAS_RISK_ENGINE,
            'ai_explanation': True,
            'report_generator': True
        }
    })


# ============================================================
# MAIN WALLET ANALYSIS ENDPOINT
# ============================================================

@app.route('/api/wallet/<address>', methods=['GET'])
def analyze_wallet(address):
    """
    Complete wallet forensic analysis.
    
    Query params:
        ?blockchain=ethereum|bitcoin (optional, auto-detected)
    """
    start_time = time.time()
    
    try:
        blockchain = request.args.get('blockchain', 'auto')
        
        print(f"\n{'='*60}")
        print(f"[API] Analyze {address}")
        print(f"   Blockchain: {blockchain}")
        print(f"{'='*60}\n")
        
        # Step 1: Fetch blockchain data
        print("[1/7] Fetching blockchain data...")
        fetcher = BlockchainForensics()
        blockchain_data = fetcher.analyze_wallet(
            address, 
            blockchain=blockchain,
            save_to_neo4j=HAS_NEO4J,
            save_to_json=False
        )
        
        if not blockchain_data:
            return jsonify({
                'error': True,
                'message': 'Failed to fetch wallet data. Check address format.',
                'code': 'FETCH_FAILED'
            }), 500
        
        detected_blockchain = blockchain_data.get('blockchain', 'ethereum')
        
        # Step 2: Calculate statistics
        print("[2/7] Calculating statistics...")
        stats = calculate_wallet_stats(blockchain_data)
        
        # Step 3: Run risk engine
        print("[3/7] Running risk analysis...")
        risk_data = run_risk_analysis(blockchain_data, stats)
        
        # Update stats with risk data
        stats['riskScore'] = risk_data.get('overall_risk', 50)
        stats['riskLevel'] = risk_data.get('risk_band', 'MEDIUM')
        
        # Step 4: Get graph data
        print("[4/7] Extracting graph data...")
        graph_data = get_wallet_graph_data(address, blockchain_data)
        
        # Step 5: Get cluster info
        print("[5/7] Getting cluster information...")
        cluster_info = get_wallet_clusters_info(address)
        
        # Step 6: Generate AI explanations
        print("[6/7] Generating AI explanations...")
        wallet_stats_for_ai = {
            'total_transactions': stats.get('totalTransactions', 0),
            'total_volume': stats.get('totalVolumeNumeric', 0),
            'connected_wallets': graph_data.get('connectedWallets', 0),
            'suspicious_activities': stats.get('suspiciousActivities', 0)
        }
        ai_insights = generate_ai_explanation(
            risk_data, wallet_stats_for_ai,
            cluster_info, detected_blockchain
        )
        
        # Step 7: Generate graph explanation
        print("[7/8] Generating graph explanation...")
        graph_explanation = generate_graph_explanation(
            graph_data.get('graphData', {'nodes': [], 'edges': []}),
            risk_data,
            detected_blockchain
        )

        # Step 8: Transform transactions
        print("[8/8] Transforming transaction data...")
        transactions = transform_transactions(blockchain_data)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Build response
        response = {
            'address': address,
            'blockchain': detected_blockchain,
            'riskScore': stats.get('riskScore', 50),
            'riskLevel': stats.get('riskLevel', 'MEDIUM'),
            'totalTransactions': stats.get('totalTransactions', 0),
            'totalVolume': stats.get('totalVolume', '0'),
            'balance': stats.get('balance', '0'),
            'connectedWallets': graph_data.get('connectedWallets', 0),
            'suspiciousActivities': stats.get('suspiciousActivities', 0),
            'clusterId': cluster_info.get('clusterId', None),
            'transactions': transactions,
            'graphData': graph_data.get('graphData', {'nodes': [], 'edges': []}),
            'aiInsights': ai_insights,
            'graphExplanation': graph_explanation,
            'riskBreakdown': risk_data.get('factor_breakdown', {}),
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'processing_time_ms': processing_time,
                'ai_model': ai_insights.get('ai_model', 'rule-based')
            }
        }
        
        print(f"\n[OK] Analysis complete in {processing_time}ms")
        print(f"   Risk: {stats.get('riskScore')}/100 ({stats.get('riskLevel')})")
        print(f"   Transactions: {stats.get('totalTransactions')}")
        print(f"   Graph nodes: {len(graph_data.get('graphData', {}).get('nodes', []))}\n")
        
        return jsonify(response)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\n[ERR] Error analyzing wallet: {e}")
        print(error_trace)
        
        return jsonify({
            'error': True,
            'message': str(e),
            'code': 'ANALYSIS_FAILED',
            'details': {
                'address': address,
                'trace': error_trace if app.debug else None
            }
        }), 500


# ============================================================
# REPORT GENERATION ENDPOINT
# ============================================================

@app.route('/api/report/<address>', methods=['GET'])
def generate_report(address):
    """Generate HTML forensic report for a wallet."""
    try:
        blockchain = request.args.get('blockchain', 'auto')
        
        # Fetch and analyze
        fetcher = BlockchainForensics()
        blockchain_data = fetcher.analyze_wallet(address, blockchain=blockchain, save_to_neo4j=False)
        
        if not blockchain_data:
            return jsonify({'error': 'Failed to fetch wallet data'}), 500
        
        detected_blockchain = blockchain_data.get('blockchain', 'ethereum')
        stats = calculate_wallet_stats(blockchain_data)
        risk_data = run_risk_analysis(blockchain_data, stats)
        transactions = transform_transactions(blockchain_data)
        
        wallet_stats_for_ai = {
            'total_transactions': stats.get('totalTransactions', 0),
            'total_volume': stats.get('totalVolumeNumeric', 0),
            'connected_wallets': 0,
            'suspicious_activities': stats.get('suspiciousActivities', 0)
        }
        ai_insights = generate_ai_explanation(risk_data, wallet_stats_for_ai, blockchain=detected_blockchain)
        
        # Generate HTML report
        html_report = report_gen.generate_report(
            address=address,
            blockchain=detected_blockchain,
            risk_data=risk_data,
            wallet_stats=wallet_stats_for_ai,
            transactions=transactions,
            ai_explanation=ai_insights
        )
        
        return Response(html_report, mimetype='text/html')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def run_risk_analysis(blockchain_data, stats):
    """Run the risk engine on blockchain data."""
    if not HAS_RISK_ENGINE:
        # Placeholder risk when engine unavailable
        score = min(100, max(0, stats.get('totalTransactions', 0) // 10 + 30))
        return {
            'overall_risk': score,
            'risk_band': 'HIGH' if score >= 70 else 'MEDIUM' if score >= 40 else 'LOW',
            'factor_breakdown': {
                'transaction_velocity': {'score': score * 0.15, 'reason': 'Based on transaction count'},
                'amount_anomaly': {'score': score * 0.1, 'reason': 'Estimated from volume patterns'},
            }
        }
    
    try:
        # Build wallet dict for risk engine
        blockchain = blockchain_data.get('blockchain', 'ethereum')
        
        if blockchain == 'ethereum':
            txs = blockchain_data.get('normal_transactions', [])
            incoming = []
            outgoing = []
            timestamps = []
            wallet_addr = blockchain_data.get('wallet_address', '').lower()
            
            for tx in txs:
                try:
                    value = float(tx.get('value', 0)) / 1e18
                    ts = int(tx.get('timeStamp', 0))
                    if ts > 0:
                        timestamps.append(ts)
                    if tx.get('from', '').lower() == wallet_addr:
                        outgoing.append(value)
                    else:
                        incoming.append(value)
                except:
                    pass
            
            wallet_dict = {
                'address': wallet_addr,
                'transactions': txs,
                'incoming_amounts': incoming or [0],
                'outgoing_amounts': outgoing or [0],
                'tx_timestamps': sorted(timestamps) or [0],
                'cluster_size': 1,
                'avg_degree': len(set(tx.get('from', '') for tx in txs)) / max(len(txs), 1),
                'days_inactive': 0,
                'post_reactivation_tx_per_day': 0
            }
        else:
            # Bitcoin — normalize transactions to match risk engine expectations
            txs = blockchain_data.get('transactions', [])
            wallet_addr = blockchain_data.get('wallet_address', '')
            
            # Build Ethereum-compatible transaction list for risk factors
            normalized_txs = []
            incoming_amounts = []
            outgoing_amounts = []
            timestamps = []
            
            for tx in txs:
                btc_val = tx.get('value_btc', 0)
                ts = tx.get('time', 0)
                if ts > 0:
                    timestamps.append(ts)
                
                # Normalize: set 'from' to wallet address so factors detect outgoing txs
                # Bitcoin UTXO model: all fetched txs involve this wallet
                normalized_txs.append({
                    'from': wallet_addr,
                    'to': 'counterparty',
                    'value': str(int(btc_val * 1e8)),  # Convert BTC to satoshi string (like wei)
                    'timeStamp': str(ts)
                })
                
                # Treat all tx values as outgoing for risk analysis
                if btc_val > 0:
                    outgoing_amounts.append(btc_val)
                else:
                    incoming_amounts.append(abs(btc_val) if btc_val else 0.01)
            
            # Calculate days inactive
            days_inactive = 0
            if timestamps:
                from datetime import datetime as dt
                last_tx_time = max(timestamps)
                days_inactive = (dt.now().timestamp() - last_tx_time) / 86400
            
            wallet_dict = {
                'address': wallet_addr,
                'transactions': normalized_txs,
                'incoming_amounts': incoming_amounts or [0],
                'outgoing_amounts': outgoing_amounts or [0],
                'tx_timestamps': sorted(timestamps) or [0],
                'cluster_size': len(set(tx.get('hash', '') for tx in txs)),
                'avg_degree': min(10, len(txs) / max(1, len(set(ts for ts in timestamps)))),
                'days_inactive': max(0, int(days_inactive)),
                'post_reactivation_tx_per_day': len(txs) / max(1, (max(timestamps) - min(timestamps)) / 86400) if len(timestamps) >= 2 else 0
            }
        
        result = risk_engine(wallet_dict)
        return result
        
    except Exception as e:
        print(f"[WARN] Risk engine error: {e}")
        return {
            'overall_risk': 50,
            'risk_band': 'MEDIUM',
            'factor_breakdown': {}
        }


def get_wallet_graph_data(address, blockchain_data=None):
    """Extract graph visualization data."""
    
    # Try Neo4j first
    if HAS_NEO4J:
        try:
            with Neo4jConnection() as conn:
                query = """
                MATCH (w:Wallet {address: $address})
                OPTIONAL MATCH (w)-[r1:SENT|RECEIVED_BY]-(t:Transaction)-[r2:SENT|RECEIVED_BY]-(connected:Wallet)
                WHERE connected.address <> w.address
                WITH w, connected, count(DISTINCT t) as tx_count, sum(t.value) as total_value
                RETURN w, 
                       collect({
                           address: connected.address,
                           risk: coalesce(connected.risk_score, 50),
                           tx_count: tx_count,
                           total_value: total_value
                       }) as connections
                LIMIT 1
                """
                result = conn.execute_query(query, {'address': address})
                
                if result and len(result) > 0:
                    connections = result[0].get('connections', [])
                    # Filter out null connections
                    connections = [c for c in connections if c.get('address')]
                    
                    if connections:  # Only use Neo4j graph if we got actual connections
                        nodes = [{'id': address[:12], 'label': 'Target Wallet', 'type': 'target', 'risk': 67, 'fullAddress': address}]
                        edges = []
                        
                        for i, c in enumerate(connections[:15], 1):
                            risk = c.get('risk', 50)
                            node_type = 'high-risk' if risk >= 70 else 'medium-risk' if risk >= 40 else 'low-risk'
                            nodes.append({
                                'id': c['address'][:12],
                                'label': f"Wallet {i}",
                                'type': node_type,
                                'risk': risk,
                                'fullAddress': c['address']
                            })
                            edges.append({
                                'from': address[:12],
                                'to': c['address'][:12],
                                'value': c.get('tx_count', 1),
                                'label': f"{c.get('tx_count', 0)} TXs"
                            })
                        
                        return {'connectedWallets': len(connections), 'graphData': {'nodes': nodes, 'edges': edges}}
        except Exception as e:
            print(f"[WARN] Neo4j graph query failed: {e}")
    
    # Fallback: Build graph from blockchain data
    if blockchain_data:
        return build_graph_from_blockchain_data(address, blockchain_data)
    
    return {'connectedWallets': 0, 'graphData': {'nodes': [], 'edges': []}}


def build_graph_from_blockchain_data(address, blockchain_data):
    """Build graph visualization from raw blockchain data."""
    blockchain = blockchain_data.get('blockchain', 'ethereum')
    nodes = [{'id': 'target', 'label': 'Target Wallet', 'type': 'target', 'risk': 50, 'fullAddress': address}]
    edges = []
    seen_wallets = set()
    
    if blockchain == 'ethereum':
        txs = blockchain_data.get('normal_transactions', [])
        wallet_lower = address.lower()
        
        for tx in txs[:100]:
            counterparty = tx.get('to', '') if tx.get('from', '').lower() == wallet_lower else tx.get('from', '')
            if counterparty and counterparty.lower() != wallet_lower and counterparty not in seen_wallets:
                seen_wallets.add(counterparty)
                if len(nodes) >= 26:
                    break
                
                node_id = f"w{len(nodes)}"
                nodes.append({
                    'id': node_id,
                    'label': f"Wallet {len(nodes)}",
                    'type': 'medium-risk',
                    'risk': 50,
                    'fullAddress': counterparty
                })
                
                direction = 'target' if tx.get('from', '').lower() == wallet_lower else node_id
                edges.append({
                    'from': 'target' if tx.get('from', '').lower() == wallet_lower else node_id,
                    'to': node_id if tx.get('from', '').lower() == wallet_lower else 'target',
                    'value': 1,
                    'label': f"{float(tx.get('value', 0)) / 1e18:.4f} ETH"
                })
    
    elif blockchain == 'bitcoin':
        txs = blockchain_data.get('transactions', [])
        for i, tx in enumerate(txs[:25]):
            node_id = f"btx{i+1}"
            btc_val = tx.get('value_btc', 0)
            risk_val = 70 if btc_val > 10 else 50 if btc_val > 1 else 30
            node_type = 'high-risk' if btc_val > 10 else 'medium-risk' if btc_val > 1 else 'low-risk'
            nodes.append({
                'id': node_id,
                'label': f"TX {i+1}",
                'type': node_type,
                'risk': risk_val
            })
            edges.append({
                'from': 'target',
                'to': node_id,
                'value': max(1, int(btc_val)),
                'label': f"{btc_val:.4f} BTC"
            })
    
    return {'connectedWallets': len(nodes) - 1, 'graphData': {'nodes': nodes, 'edges': edges}}


def get_wallet_clusters_info(address):
    """Get cluster information for wallet."""
    if not HAS_NEO4J:
        return {'clusterId': None}
    
    try:
        with Neo4jConnection() as conn:
            query = """
            MATCH (w:Wallet {address: $address})
            OPTIONAL MATCH (w)-[r:BELONGS_TO]->(c:Cluster)
            RETURN c.cluster_id as cluster_id, 
                   c.algorithm as algorithm,
                   c.size as size
            LIMIT 1
            """
            result = conn.execute_query(query, {'address': address})
            
            if result and len(result) > 0 and result[0].get('cluster_id'):
                return {
                    'clusterId': result[0]['cluster_id'],
                    'algorithm': result[0].get('algorithm', 'unknown'),
                    'size': result[0].get('size', 0)
                }
            return {'clusterId': None}
    except Exception as e:
        print(f"[WARN] Cluster info query failed: {e}")
        return {'clusterId': None}


def calculate_wallet_stats(blockchain_data):
    """Calculate wallet statistics from blockchain data."""
    blockchain = blockchain_data.get('blockchain', 'unknown')
    
    if blockchain == 'ethereum':
        balance = blockchain_data.get('balance', {})
        if isinstance(balance, dict):
            balance_eth = balance.get('eth', 0)
        else:
            balance_eth = float(balance) if balance else 0
            
        normal_txs = blockchain_data.get('normal_transactions', [])
        internal_txs = blockchain_data.get('internal_transactions', [])
        total_txs = len(normal_txs) + len(internal_txs)
        
        total_volume = 0
        suspicious = 0
        for tx in normal_txs:
            try:
                value_wei = float(tx.get('value', 0))
                value_eth = value_wei / 1e18
                total_volume += value_eth
                # Flag high-value transactions
                if value_eth > 100:
                    suspicious += 1
            except:
                pass
        
        return {
            'balance': f"{balance_eth:.4f} ETH",
            'totalTransactions': total_txs,
            'totalVolume': f"{total_volume:.2f} ETH",
            'totalVolumeNumeric': total_volume,
            'riskScore': 50,
            'riskLevel': 'MEDIUM',
            'suspiciousActivities': suspicious
        }
    
    elif blockchain == 'bitcoin':
        balance = blockchain_data.get('balance', 0)
        txs = blockchain_data.get('transactions', [])
        
        # Extract BTC balance from dict or raw value
        if isinstance(balance, dict):
            balance_btc = balance.get('btc', 0)
        elif isinstance(balance, (int, float)):
            balance_btc = balance / 1e8
        else:
            balance_btc = 0
        
        # Calculate total volume from transactions
        total_volume_btc = 0
        suspicious = 0
        for tx in txs:
            try:
                val = float(tx.get('value_btc', 0))
                total_volume_btc += val
                if val > 10:  # Flag large BTC transactions
                    suspicious += 1
            except (ValueError, TypeError):
                pass
        
        return {
            'balance': f"{balance_btc:.8f} BTC",
            'totalTransactions': len(txs),
            'totalVolume': f"{total_volume_btc:.4f} BTC",
            'totalVolumeNumeric': total_volume_btc,
            'riskScore': 50,
            'riskLevel': 'MEDIUM',
            'suspiciousActivities': suspicious
        }
    
    return {
        'balance': '0', 'totalTransactions': 0,
        'totalVolume': '0', 'totalVolumeNumeric': 0,
        'riskScore': 0, 'riskLevel': 'UNKNOWN',
        'suspiciousActivities': 0
    }


def transform_transactions(blockchain_data):
    """Transform blockchain transactions to frontend format."""
    blockchain = blockchain_data.get('blockchain', 'unknown')
    wallet_address = blockchain_data.get('wallet_address', '')
    transactions = []
    
    if blockchain == 'ethereum':
        normal_txs = blockchain_data.get('normal_transactions', [])
        
        for i, tx in enumerate(normal_txs, 1):
            try:
                value_wei = float(tx.get('value', 0))
                value_eth = value_wei / 1e18
                is_sent = tx.get('from', '').lower() == wallet_address.lower()
                
                transactions.append({
                    'id': f"tx-{i}",
                    'hash': tx.get('hash', 'N/A'),
                    'type': 'Sent' if is_sent else 'Received',
                    'amount': f"{value_eth:.4f} ETH",
                    'from': tx.get('from', 'N/A')[:12] + '...',
                    'to': tx.get('to', 'N/A')[:12] + '...',
                    'timestamp': datetime.fromtimestamp(int(tx.get('timeStamp', 0))).isoformat(),
                    'status': 'Confirmed' if tx.get('txreceipt_status') == '1' else 'Confirmed',
                    'risk': 50
                })
            except Exception as e:
                continue
    
    elif blockchain == 'bitcoin':
        btc_txs = blockchain_data.get('transactions', [])
        
        for i, tx in enumerate(btc_txs, 1):
            try:
                # Use value_btc from fetch_bitcoin_data, fallback to value_satoshi
                btc_val = tx.get('value_btc', 0)
                if btc_val == 0 and tx.get('value_satoshi'):
                    btc_val = tx.get('value_satoshi', 0) / 1e8
                
                in_count = tx.get('inputs', 0)
                out_count = tx.get('outputs', 0)
                
                transactions.append({
                    'id': f"tx-{i}",
                    'hash': tx.get('hash', 'N/A'),
                    'type': 'Transaction',
                    'amount': f"{btc_val:.8f} BTC",
                    'from': f"{in_count} input{'s' if in_count != 1 else ''}",
                    'to': f"{out_count} output{'s' if out_count != 1 else ''}",
                    'timestamp': datetime.fromtimestamp(tx.get('time', 0)).isoformat() if tx.get('time') else 'N/A',
                    'status': 'Confirmed',
                    'risk': 50
                })
            except:
                continue
    
    return transactions


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print(">> Blockchain Forensics API Server v2.0")
    print("="*60)
    print("\n   Endpoints:")
    print("   GET /api/health          -- Health check")
    print("   GET /api/wallet/<address> -- Full wallet analysis")
    print("   GET /api/report/<address> -- HTML forensic report")
    print(f"\n   Modules:")
    print(f"   Blockchain Fetcher: OK")
    print(f"   Neo4j Graph:       {'OK' if HAS_NEO4J else 'UNAVAILABLE'}")
    print(f"   Risk Engine:       {'OK' if HAS_RISK_ENGINE else 'UNAVAILABLE'}")
    print(f"   AI Explanation:    OK")
    print(f"   Report Generator:  OK")
    print("\n   CORS enabled for: http://localhost:5173")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
