"""
Unified Blockchain Data Fetcher
Supports both Bitcoin and Ethereum blockchain analysis
Authors: Isha (Ethereum), Shreya (Bitcoin), Mohit (Integration)
"""

import requests
import json
from datetime import datetime
import os

class BlockchainForensics:
    def __init__(self):
        # Try to get API key from environment, fallback to hardcoded (for development only)
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.etherscan_base_url = "https://api.etherscan.io/v2/api"
        self.bitcoin_base_url = "https://blockchain.info"
    
    def fetch_ethereum_data(self, wallet_address):
        """
        Fetch Ethereum wallet data using Etherscan API
        Author: Isha
        """
        print(f"\n[ETH] Fetching Ethereum data for: {wallet_address}")
        
        result = {
            "blockchain": "ethereum",
            "wallet_address": wallet_address,
            "scan_time": datetime.now().isoformat(),
            "balance": None,
            "normal_transactions": [],
            "internal_transactions": [],
            "token_transfers": []
        }
        
        # 1. Get Wallet Balance
        print("  Fetching balance...")
        balance_params = {
            "chainid": 1,
            "module": "account",
            "action": "balance",
            "address": wallet_address,
            "tag": "latest",
            "apikey": self.etherscan_api_key
        }
        
        try:
            balance_response = requests.get(self.etherscan_base_url, params=balance_params)
            balance_data = balance_response.json()
            
            if balance_data["status"] == "1":
                balance_wei = int(balance_data["result"])
                balance_eth = balance_wei / 10**18
                result["balance"] = {
                    "wei": balance_wei,
                    "eth": balance_eth
                }
                print(f"  [OK] Balance: {balance_eth:.4f} ETH")
        except Exception as e:
            print(f"  [WARN] Balance fetch failed: {e}")
        
        # 2. Get Normal Transactions
        print("  Fetching normal transactions...")
        tx_params = {
            "chainid": 1,
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 5000,
            "sort": "desc",
            "apikey": self.etherscan_api_key
        }
        
        try:
            tx_response = requests.get(self.etherscan_base_url, params=tx_params)
            tx_data = tx_response.json()
            
            if tx_data["status"] == "1":
                result["normal_transactions"] = tx_data["result"]
                print(f"  [OK] Found {len(tx_data['result'])} normal transactions")
        except Exception as e:
            print(f"  [WARN] Normal transactions fetch failed: {e}")
        
        # 3. Get Internal Transactions
        print("  Fetching internal transactions...")
        internal_params = {
            "chainid": 1,
            "module": "account",
            "action": "txlistinternal",
            "address": wallet_address,
            "page": 1,
            "offset": 5000,
            "sort": "desc",
            "apikey": self.etherscan_api_key
        }
        
        try:
            internal_response = requests.get(self.etherscan_base_url, params=internal_params)
            internal_data = internal_response.json()
            
            if internal_data["status"] == "1":
                result["internal_transactions"] = internal_data["result"]
                print(f"  [OK] Found {len(internal_data['result'])} internal transactions")
        except Exception as e:
            print(f"  [WARN] Internal transactions fetch failed: {e}")
        
        # 4. Get Token Transfers
        print("  Fetching token transfers...")
        token_params = {
            "chainid": 1,
            "module": "account",
            "action": "tokentx",
            "address": wallet_address,
            "page": 1,
            "offset": 5000,
            "sort": "desc",
            "apikey": self.etherscan_api_key
        }
        
        try:
            token_response = requests.get(self.etherscan_base_url, params=token_params)
            token_data = token_response.json()
            
            if token_data["status"] == "1":
                result["token_transfers"] = token_data["result"]
                print(f"  [OK] Found {len(token_data['result'])} token transfers")
        except Exception as e:
            print(f"  [WARN] Token transfers fetch failed: {e}")
        
        return result
    
    def fetch_bitcoin_data(self, wallet_address):
        """
        Fetch Bitcoin wallet data using blockchain.info API
        Author: Shreya
        """
        print(f"\n[BTC] Fetching Bitcoin data for: {wallet_address}")
        
        result = {
            "blockchain": "bitcoin",
            "wallet_address": wallet_address,
            "scan_time": datetime.now().isoformat(),
            "balance": None,
            "transactions": []
        }
        
        try:
            # Fetch wallet data from blockchain.info
            url = f"{self.bitcoin_base_url}/rawaddr/{wallet_address}"
            response = requests.get(url)
            data = response.json()
            
            # Extract balance
            balance_satoshi = data.get("final_balance", 0)
            balance_btc = balance_satoshi / 100000000
            result["balance"] = {
                "satoshi": balance_satoshi,
                "btc": balance_btc
            }
            print(f"  [OK] Balance: {balance_btc:.8f} BTC")
            
            # Extract transactions
            transactions = []
            for tx in data.get("txs", []):
                tx_time = datetime.fromtimestamp(tx["time"]).strftime("%Y-%m-%d %H:%M:%S")
                total_out = sum(out["value"] for out in tx["out"])
                btc_amount = total_out / 100000000
                
                transactions.append({
                    "hash": tx["hash"],
                    "time": tx["time"],
                    "formatted_time": tx_time,
                    "value_satoshi": total_out,
                    "value_btc": btc_amount,
                    "inputs": len(tx.get("inputs", [])),
                    "outputs": len(tx.get("out", []))
                })
            
            result["transactions"] = transactions
            print(f"  [OK] Found {len(transactions)} transactions")
            
        except Exception as e:
            print(f"  [WARN] Bitcoin data fetch failed: {e}")
        
        return result
    
    def analyze_wallet(self, wallet_address, blockchain="auto", save_to_neo4j=True, save_to_json=False):
        """
        Automatically detect blockchain type and fetch appropriate data
        
        Args:
            wallet_address: Wallet address to analyze
            blockchain: "auto", "bitcoin", or "ethereum"  
            save_to_neo4j: Save data to Neo4j graph database (default: True)
            save_to_json: Also save to JSON file for debugging (default: False)
        """
        # Auto-detect blockchain type
        if blockchain == "auto":
            if wallet_address.startswith("0x") and len(wallet_address) == 42:
                blockchain = "ethereum"
            elif wallet_address.startswith("bc1") or wallet_address.startswith("tb1"):
                # Bech32 / SegWit Bitcoin address
                blockchain = "bitcoin"
            elif len(wallet_address) >= 26 and len(wallet_address) <= 35:
                # Legacy P2PKH (1...) or P2SH (3...) Bitcoin address
                blockchain = "bitcoin"
            else:
                raise ValueError("Could not auto-detect blockchain type. Please specify 'bitcoin' or 'ethereum'.")
        
        print(f"\n{'='*60}")
        print(f">> BLOCKCHAIN FORENSIC ANALYSIS")
        print(f"{'='*60}")
        print(f"Blockchain: {blockchain.upper()}")
        print(f"Wallet: {wallet_address}")
        
        # Fetch data based on blockchain type
        if blockchain.lower() == "ethereum":
            data = self.fetch_ethereum_data(wallet_address)
        elif blockchain.lower() == "bitcoin":
            data = self.fetch_bitcoin_data(wallet_address)
        else:
            raise ValueError("Invalid blockchain type. Use 'bitcoin' or 'ethereum'.")
        
        # Save to Neo4j graph database
        if save_to_neo4j:
            try:
                from ..graph import Neo4jConnection, GraphBuilder
                
                print(f"\n  Saving to Neo4j graph database...")
                with Neo4jConnection() as neo4j_conn:
                    graph_builder = GraphBuilder(neo4j_conn)
                    graph_builder.build_graph_from_blockchain_data(data)
                
            except ImportError as e:
                print(f"  [WARN] Neo4j modules not found. Install with: pip install neo4j")
                print(f"   Falling back to JSON file...")
                save_to_json = True
            except ConnectionError as e:
                print(f"  [WARN] {e}")
                print(f"   Falling back to JSON file...")
                save_to_json = True
            except Exception as e:
                print(f"  [WARN] Neo4j save failed: {e}")
                print(f"   Falling back to JSON file...")
                save_to_json = True
        
        # Optionally save to JSON file (for debugging or if Neo4j unavailable)
        if save_to_json:
            filename = f"forensic_analysis_{blockchain}_{wallet_address[:10]}.json"
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            print(f"\n  [OK] Data also saved to JSON: {filename}")
        
        print(f"{'='*60}\n")
        
        return data



# CLI Interface
if __name__ == "__main__":
    forensics = BlockchainForensics()
    
    print("\n" + "="*60)
    print(">> UNIFIED BLOCKCHAIN FORENSICS SYSTEM")
    print("="*60)
    print("Supports: Bitcoin & Ethereum")
    print("="*60 + "\n")
    
    # Test with sample addresses
    print("Select blockchain to analyze:")
    print("1. Ethereum (default test wallet)")
    print("2. Bitcoin (default test wallet)")
    print("3. Custom address")
    
    choice = input("\nEnter choice (1-3): ").strip() or "1"
    
    if choice == "1":
        # Ethereum test wallet
        eth_wallet = "0xF977814e90dA44bFA03b6295A0616a897441aceC"
        forensics.analyze_wallet(eth_wallet, "ethereum")
        
    elif choice == "2":
        # Bitcoin test wallet
        btc_wallet = "1AJbsFZ64EpEfS5UAjAfcUG8pH8Jn3rn1F"
        forensics.analyze_wallet(btc_wallet, "bitcoin")
        
    elif choice == "3":
        wallet = input("Enter wallet address: ").strip()
        blockchain = input("Enter blockchain (bitcoin/ethereum/auto): ").strip() or "auto"
        forensics.analyze_wallet(wallet, blockchain)
    
    else:
        print("Invalid choice!")
