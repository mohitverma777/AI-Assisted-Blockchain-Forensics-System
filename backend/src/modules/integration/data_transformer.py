"""
Data Transformer
Converts blockchain fetcher output to risk engine input format
Authors: Mohit (Integration Lead)
"""

from datetime import datetime
from typing import Dict, List


def blockchain_to_risk_format(blockchain_data: Dict) -> Dict:
    """
    Transform blockchain data to risk engine format
    
    Args:
        blockchain_data: Output from BlockchainForensics.analyze_wallet()
        
    Returns:
        Dict formatted for risk_engine() input
    """
    blockchain = blockchain_data.get('blockchain', 'unknown')
    wallet_address = blockchain_data.get('wallet_address', '')
    
    if blockchain == 'ethereum':
        return _transform_ethereum_data(blockchain_data)
    elif blockchain == 'bitcoin':
        return _transform_bitcoin_data(blockchain_data)
    else:
        raise ValueError(f"Unsupported blockchain: {blockchain}")


def _transform_ethereum_data(data: Dict) -> Dict:
    """Transform Ethereum blockchain data"""
    
    wallet_address = data['wallet_address'].lower()
    normal_txs = data.get('normal_transactions', [])
    internal_txs = data.get('internal_transactions', [])
    
    # Combine all transactions
    all_transactions = normal_txs + internal_txs
    
    # Extract incoming and outgoing amounts
    incoming_amounts = []
    outgoing_amounts = []
    tx_timestamps = []
    
    for tx in all_transactions:
        value_eth = float(tx.get('value', 0)) / 1e18  # Wei to ETH
        timestamp = int(tx.get('timeStamp', 0))
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()
        
        if timestamp > 0:
            tx_timestamps.append(timestamp)
        
        if to_addr == wallet_address and value_eth > 0:
            incoming_amounts.append(value_eth)
        elif from_addr == wallet_address and value_eth > 0:
            outgoing_amounts.append(value_eth)
    
    # Sort timestamps
    tx_timestamps.sort()
    
    return {
        'address': data['wallet_address'],
        'transactions': all_transactions,
        'incoming_amounts': incoming_amounts,
        'outgoing_amounts': outgoing_amounts,
        'tx_timestamps': tx_timestamps,
        # Graph metrics will be filled by graph_analyzer
        'cluster_size': 0,
        'avg_degree': 0.0,
        'days_inactive': 0,
        'post_reactivation_tx_per_day': 0
    }


def _transform_bitcoin_data(data: Dict) -> Dict:
    """Transform Bitcoin blockchain data"""
    
    wallet_address = data['wallet_address']
    transactions = data.get('transactions', [])
    
    # Extract amounts and timestamps
    incoming_amounts = []
    outgoing_amounts = []
    tx_timestamps = []
    
    for tx in transactions:
        # Bitcoin transactions have inputs and outputs
        value_btc = tx.get('value_btc', 0.0)
        timestamp = int(tx.get('time', 0))
        
        if timestamp > 0:
            tx_timestamps.append(timestamp)
        
        # Simplified: assume positive values are incoming
        if value_btc > 0:
            incoming_amounts.append(value_btc)
        elif value_btc < 0:
            outgoing_amounts.append(abs(value_btc))
    
    # Sort timestamps
    tx_timestamps.sort()
    
    return {
        'address': data['wallet_address'],
        'transactions': transactions,
        'incoming_amounts': incoming_amounts,
        'outgoing_amounts': outgoing_amounts,
        'tx_timestamps': tx_timestamps,
        # Graph metrics will be filled by graph_analyzer
        'cluster_size': 0,
        'avg_degree': 0.0,
        'days_inactive': 0,
        'post_reactivation_tx_per_day': 0
    }


def extract_transaction_summary(blockchain_data: Dict) -> Dict:
    """
    Extract high-level transaction summary
    
    Returns:
        Dict with transaction counts and volume
    """
    blockchain = blockchain_data.get('blockchain', 'unknown')
    
    if blockchain == 'ethereum':
        normal_count = len(blockchain_data.get('normal_transactions', []))
        internal_count = len(blockchain_data.get('internal_transactions', []))
        token_count = len(blockchain_data.get('token_transfers', []))
        
        return {
            'total_transactions': normal_count + internal_count,
            'normal_transactions': normal_count,
            'internal_transactions': internal_count,
            'token_transfers': token_count
        }
    elif blockchain == 'bitcoin':
        return {
            'total_transactions': len(blockchain_data.get('transactions', [])),
            'normal_transactions': len(blockchain_data.get('transactions', [])),
            'internal_transactions': 0,
            'token_transfers': 0
        }
    
    return {'total_transactions': 0}


# Test function
if __name__ == '__main__':
    # Test with sample Ethereum data
    sample_eth_data = {
        'blockchain': 'ethereum',
        'wallet_address': '0xF977814e90dA44bFA03b6295A0616a897441aceC',
        'balance': {'eth': 1.23},
        'normal_transactions': [
            {
                'from': '0xabc123',
                'to': '0xF977814e90dA44bFA03b6295A0616a897441aceC',
                'value': '1000000000000000000',  # 1 ETH
                'timeStamp': '1640995200'
            },
            {
                'from': '0xF977814e90dA44bFA03b6295A0616a897441aceC',
                'to': '0xdef456',
                'value': '500000000000000000',  # 0.5 ETH
                'timeStamp': '1641081600'
            }
        ],
        'internal_transactions': []
    }
    
    print("Testing data transformer...")
    result = blockchain_to_risk_format(sample_eth_data)
    
    print(f"✅ Address: {result['address']}")
    print(f"✅ Incoming amounts: {result['incoming_amounts']}")
    print(f"✅ Outgoing amounts: {result['outgoing_amounts']}")
    print(f"✅ Timestamps: {result['tx_timestamps']}")
    print("\n✅ Data transformer test passed!")
