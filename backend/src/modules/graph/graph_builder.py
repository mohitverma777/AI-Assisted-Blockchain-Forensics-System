"""
Blockchain Graph Builder
Transforms blockchain data into Neo4j graph nodes and relationships
Authors: Krusha (Primary), Isha (Support), Mohit (Integration)
"""

from datetime import datetime
from .neo4j_connection import Neo4jConnection


class GraphBuilder:
    """
    Builds graph representation of blockchain data in Neo4j
    
    Graph Schema:
        - Wallet nodes: (address, blockchain, balance, timestamps)
        - Transaction nodes: (hash, timestamp, value, blockchain)
        - Relationships: SENT, RECEIVED_BY, TRANSACTED_WITH
    """
    
    def __init__(self, connection):
        """
        Initialize graph builder with Neo4j connection
        
        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection
        self._create_constraints()
    
    def _create_constraints(self):
        """Create uniqueness constraints for wallet addresses and transaction hashes"""
        try:
            # Unique constraint on wallet address
            self.conn.execute_query(
                "CREATE CONSTRAINT wallet_address_unique IF NOT EXISTS "
                "FOR (w:Wallet) REQUIRE w.address IS UNIQUE"
            )
            
            # Unique constraint on transaction hash
            self.conn.execute_query(
                "CREATE CONSTRAINT transaction_hash_unique IF NOT EXISTS "
                "FOR (t:Transaction) REQUIRE t.hash IS UNIQUE"
            )
            
            print("✅ Database constraints created/verified")
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")
    
    def create_wallet_node(self, wallet_data):
        """
        Create or update a wallet node in Neo4j
        
        Args:
            wallet_data: Dictionary with wallet information
                - wallet_address: Wallet address
                - blockchain: "bitcoin" or "ethereum"
                - balance: Balance information dict
                - scan_time: Scan timestamp
                
        Returns:
            Created/updated wallet node properties
        """
        print(f"💾 Creating/updating wallet node: {wallet_data['wallet_address'][:10]}...")
        
        # Extract balance value
        balance_value = 0.0
        balance_unit = ""
        
        if wallet_data.get("balance"):
            if wallet_data["blockchain"] == "ethereum":
                balance_value = wallet_data["balance"].get("eth", 0.0)
                balance_unit = "ETH"
            elif wallet_data["blockchain"] == "bitcoin":
                balance_value = wallet_data["balance"].get("btc", 0.0)
                balance_unit = "BTC"
        
        query = """
        MERGE (w:Wallet {address: $address})
        ON CREATE SET
            w.blockchain = $blockchain,
            w.balance = $balance,
            w.balance_unit = $balance_unit,
            w.first_seen = datetime($timestamp),
            w.last_updated = datetime($timestamp),
            w.total_transactions = 0
        ON MATCH SET
            w.balance = $balance,
            w.last_updated = datetime($timestamp)
        RETURN w
        """
        
        parameters = {
            "address": wallet_data["wallet_address"],
            "blockchain": wallet_data["blockchain"],
            "balance": balance_value,
            "balance_unit": balance_unit,
            "timestamp": wallet_data.get("scan_time", datetime.now().isoformat())
        }
        
        result = self.conn.execute_query(query, parameters)
        print(f"✅ Wallet node created/updated")
        return result[0]["w"] if result else None
    
    def create_transaction_node(self, tx_data, blockchain):
        """
        Create a transaction node in Neo4j
        
        Args:
            tx_data: Transaction data dictionary
            blockchain: "bitcoin" or "ethereum"
            
        Returns:
            Created transaction node
        """
        # Common fields
        tx_hash = tx_data.get("hash")
        if not tx_hash:
            return None
        
        # Prepare transaction properties
        if blockchain == "ethereum":
            timestamp = int(tx_data.get("timeStamp", 0))
            value = int(tx_data.get("value", 0)) / 1e18  # Wei to ETH
            block_number = int(tx_data.get("blockNumber", 0))
            from_address = tx_data.get("from", "")
            to_address = tx_data.get("to", "")
            gas_used = int(tx_data.get("gasUsed", 0))
            
            query = """
            MERGE (t:Transaction {hash: $hash})
            ON CREATE SET
                t.timestamp = datetime({epochSeconds: $timestamp}),
                t.value = $value,
                t.blockchain = $blockchain,
                t.block_number = $block_number,
                t.from_address = $from_address,
                t.to_address = $to_address,
                t.gas_used = $gas_used,
                t.created_at = datetime()
            RETURN t
            """
            
            parameters = {
                "hash": tx_hash,
                "timestamp": timestamp,
                "value": value,
                "blockchain": blockchain,
                "block_number": block_number,
                "from_address": from_address,
                "to_address": to_address,
                "gas_used": gas_used
            }
            
        elif blockchain == "bitcoin":
            timestamp = int(tx_data.get("time", 0))
            value_btc = tx_data.get("value_btc", 0.0)
            
            query = """
            MERGE (t:Transaction {hash: $hash})
            ON CREATE SET
                t.timestamp = datetime({epochSeconds: $timestamp}),
                t.value = $value,
                t.blockchain = $blockchain,
                t.created_at = datetime()
            RETURN t
            """
            
            parameters = {
                "hash": tx_hash,
                "timestamp": timestamp,
                "value": value_btc,
                "blockchain": blockchain
            }
        else:
            return None
        
        result = self.conn.execute_query(query, parameters)
        return result[0]["t"] if result else None
    
    def create_transaction_relationships(self, wallet_address, transactions, blockchain):
        """
        Create relationships between wallet and transactions
        
        Args:
            wallet_address: Wallet address
            transactions: List of transaction data
            blockchain: "bitcoin" or "ethereum"
        """
        print(f"🔗 Creating transaction relationships for {len(transactions)} transactions...")
        
        created_count = 0
        
        for tx in transactions:
            tx_hash = tx.get("hash")
            if not tx_hash:
                continue
            
            # Create transaction node
            self.create_transaction_node(tx, blockchain)
            
            if blockchain == "ethereum":
                from_addr = tx.get("from", "").lower()
                to_addr = tx.get("to", "").lower()
                wallet_lower = wallet_address.lower()
                value = int(tx.get("value", 0)) / 1e18
                timestamp = int(tx.get("timeStamp", 0))
                
                # Determine relationship direction
                if from_addr == wallet_lower:
                    # Wallet sent this transaction
                    query = """
                    MATCH (w:Wallet {address: $wallet})
                    MATCH (t:Transaction {hash: $hash})
                    MERGE (w)-[r:SENT]->(t)
                    ON CREATE SET
                        r.amount = $amount,
                        r.timestamp = datetime({epochSeconds: $timestamp})
                    """
                    
                    self.conn.execute_query(query, {
                        "wallet": wallet_address,
                        "hash": tx_hash,
                        "amount": value,
                        "timestamp": timestamp
                    })
                    
                    # Also create relationship to recipient wallet if it exists
                    if to_addr:
                        recipient_query = """
                        MERGE (w2:Wallet {address: $to_address})
                        ON CREATE SET
                            w2.blockchain = $blockchain,
                            w2.first_seen = datetime()
                        WITH w2
                        MATCH (t:Transaction {hash: $hash})
                        MERGE (t)-[r:RECEIVED_BY]->(w2)
                        ON CREATE SET
                            r.amount = $amount,
                            r.timestamp = datetime({epochSeconds: $timestamp})
                        """
                        
                        self.conn.execute_query(recipient_query, {
                            "to_address": to_addr,
                            "blockchain": blockchain,
                            "hash": tx_hash,
                            "amount": value,
                            "timestamp": timestamp
                        })
                
                elif to_addr == wallet_lower:
                    # Wallet received this transaction
                    query = """
                    MATCH (w:Wallet {address: $wallet})
                    MATCH (t:Transaction {hash: $hash})
                    MERGE (t)-[r:RECEIVED_BY]->(w)
                    ON CREATE SET
                        r.amount = $amount,
                        r.timestamp = datetime({epochSeconds: $timestamp})
                    """
                    
                    self.conn.execute_query(query, {
                        "wallet": wallet_address,
                        "hash": tx_hash,
                        "amount": value,
                        "timestamp": timestamp
                    })
                    
                    # Also create sender wallet node if it doesn't exist
                    if from_addr:
                        sender_query = """
                        MERGE (w1:Wallet {address: $from_address})
                        ON CREATE SET
                            w1.blockchain = $blockchain,
                            w1.first_seen = datetime()
                        WITH w1
                        MATCH (t:Transaction {hash: $hash})
                        MERGE (w1)-[r:SENT]->(t)
                        ON CREATE SET
                            r.amount = $amount,
                            r.timestamp = datetime({epochSeconds: $timestamp})
                        """
                        
                        self.conn.execute_query(sender_query, {
                            "from_address": from_addr,
                            "blockchain": blockchain,
                            "hash": tx_hash,
                            "amount": value,
                            "timestamp": timestamp
                        })
                
                created_count += 1
            
            elif blockchain == "bitcoin":
                # For Bitcoin, simpler relationship (just link to wallet)
                value = tx.get("value_btc", 0.0)
                timestamp = int(tx.get("time", 0))
                
                query = """
                MATCH (w:Wallet {address: $wallet})
                MATCH (t:Transaction {hash: $hash})
                MERGE (w)-[r:RELATED_TO]->(t)
                ON CREATE SET
                    r.amount = $amount,
                    r.timestamp = datetime({epochSeconds: $timestamp})
                """
                
                self.conn.execute_query(query, {
                    "wallet": wallet_address,
                    "hash": tx_hash,
                    "amount": value,
                    "timestamp": timestamp
                })
                
                created_count += 1
        
        # Update wallet's transaction count
        update_query = """
        MATCH (w:Wallet {address: $wallet})-[r]-(t:Transaction)
        WITH w, count(DISTINCT t) as tx_count
        SET w.total_transactions = tx_count
        RETURN tx_count
        """
        
        result = self.conn.execute_query(update_query, {"wallet": wallet_address})
        tx_count = result[0]["tx_count"] if result else 0
        
        print(f"✅ Created {created_count} transaction relationships ({tx_count} total for wallet)")
    
    def build_graph_from_blockchain_data(self, blockchain_data):
        """
        Main function to build graph from blockchain data
        
        Args:
            blockchain_data: Complete blockchain data dictionary from fetcher
        """
        print(f"\n{'='*60}")
        print(f"🔨 Building Neo4j Graph")
        print(f"{'='*60}")
        
        blockchain = blockchain_data.get("blockchain")
        wallet_address = blockchain_data.get("wallet_address")
        
        print(f"Blockchain: {blockchain.upper()}")
        print(f"Wallet: {wallet_address}")
        
        # Step 1: Create wallet node
        self.create_wallet_node(blockchain_data)
        
        # Step 2: Create transactions and relationships
        if blockchain == "ethereum":
            # Process normal transactions
            normal_txs = blockchain_data.get("normal_transactions", [])
            if normal_txs:
                print(f"\n📊 Processing {len(normal_txs)} normal transactions...")
                self.create_transaction_relationships(wallet_address, normal_txs, blockchain)
            
            # Process internal transactions
            internal_txs = blockchain_data.get("internal_transactions", [])
            if internal_txs:
                print(f"\n📊 Processing {len(internal_txs)} internal transactions...")
                self.create_transaction_relationships(wallet_address, internal_txs, blockchain)
            
            # Note: Token transfers could be added similarly
        
        elif blockchain == "bitcoin":
            transactions = blockchain_data.get("transactions", [])
            if transactions:
                print(f"\n📊 Processing {len(transactions)} Bitcoin transactions...")
                self.create_transaction_relationships(wallet_address, transactions, blockchain)
        
        print(f"\n{'='*60}")
        print(f"✅ Graph building complete!")
        
        # Print database stats
        stats = self.conn.get_database_stats()
        print(f"\n📊 Database Stats:")
        print(f"   Total Wallets: {stats['nodes']}")
        print(f"   Total Relationships: {stats['relationships']}")
        print(f"{'='*60}\n")
