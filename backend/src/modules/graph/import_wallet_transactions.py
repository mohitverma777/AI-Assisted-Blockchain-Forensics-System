"""
Neo4j import script for wallet transactions
Authors: shubham (Primary), Mohit (Integration)
"""
import json
from neo4j import GraphDatabase

# 1. LOAD JSON FILE
with open("wallet_transactions.json", "r") as f:
    data = json.load(f)

# IMPORTANT: actual transactions are inside "result"
transactions = data["result"]

# 2. CONNECT TO NEO4J
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "Shubham@20122001")  # <-- your Neo4j password
)

# 3. FUNCTION TO INSERT ONE TRANSACTION
def insert_tx(tx):
    query = """
    MERGE (w1:Wallet {address: $from})
    MERGE (w2:Wallet {address: $to})
    CREATE (w1)-[:SENT {
        amount: $amount,
        txHash: $hash,
        timestamp: $time
    }]->(w2)
    """
    with driver.session() as session:
        session.run(query, **tx)

# 4. LOOP OVER JSON DATA
for tx in transactions:
    # skip invalid records
    if not tx.get("to"):
        continue

    insert_tx({
        "from": tx["from"],
        "to": tx["to"],
        "amount": float(tx["value"]),
        "hash": tx["hash"],
        "time": tx["timeStamp"]
    })

print("✅ wallet_transactions.json imported successfully")