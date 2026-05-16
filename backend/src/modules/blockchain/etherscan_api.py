import requests
import json
import webbrowser


# ---------------- CONFIG ----------------
API_KEY = "etherscan_api_key"
TARGET_WALLET = "0xF977814e90dA44bFA03b6295A0616a897441aceC"

BASE_URL = "https://api.etherscan.io/v2/api"
CHAIN_ID = 1

print("\n🔎 STARTING BLOCKCHAIN FORENSIC SCAN...")
print("Wallet:", TARGET_WALLET)

# -----------------------------------------
# 1. GET WALLET BALANCE
# -----------------------------------------
print("\n📌 Fetching Wallet Balance...")

balance_params = {
    "chainid": CHAIN_ID,
    "module": "account",
    "action": "balance",
    "address": TARGET_WALLET,
    "tag": "latest",
    "apikey": API_KEY
}

balance_response = requests.get(BASE_URL, params=balance_params)
balance_data = balance_response.json()

if balance_data["status"] == "1":
    balance = float(balance_data["result"]) / 10**18
    print("✅ Balance:", balance, "ETH")

    # Save Balance JSON
    with open("wallet_balance.json", "w") as f:
        json.dump(balance_data, f, indent=4)

else:
    print("⚠️ Balance fetch failed!")


# -----------------------------------------
# 2. GET NORMAL TRANSACTIONS
# -----------------------------------------
print("\n📌 Fetching Normal Transactions...")

tx_params = {
    "chainid": CHAIN_ID,
    "module": "account",
    "action": "txlist",
    "address": TARGET_WALLET,
    "startblock": 0,
    "endblock": 99999999,
    "page": 1,
    "offset": 20,
    "sort": "desc",
    "apikey": API_KEY
}

tx_response = requests.get(BASE_URL, params=tx_params)
tx_data = tx_response.json()

if tx_data["status"] == "1":
    transactions = tx_data["result"]
    print("✅ Total Transactions Found:", len(transactions))

    # Print first 5
    for tx in transactions[:5]:
        print("\n🔹 Hash:", tx["hash"])
        print("   From:", tx["from"])
        print("   To:", tx["to"])
        print("   Value:", int(tx["value"]) / 10**18, "ETH")

    # Save Transactions JSON
    with open("wallet_transactions.json", "w") as f:
        json.dump(tx_data, f, indent=4)

else:
    print("⚠️ Transaction fetch failed!")


# -----------------------------------------
# 3. GET INTERNAL TRANSACTIONS
# -----------------------------------------
print("\n📌 Fetching Internal Transactions...")

internal_params = {
    "chainid": CHAIN_ID,
    "module": "account",
    "action": "txlistinternal",
    "address": TARGET_WALLET,
    "page": 1,
    "offset": 20,
    "sort": "desc",
    "apikey": API_KEY
}

internal_response = requests.get(BASE_URL, params=internal_params)
internal_data = internal_response.json()

if internal_data["status"] == "1":
    print("✅ Internal Transactions Found:", len(internal_data["result"]))

    with open("wallet_internal_transactions.json", "w") as f:
        json.dump(internal_data, f, indent=4)

else:
    print("⚠️ Internal transaction fetch failed!")


# -----------------------------------------
# 4. GET ERC20 TOKEN TRANSFERS
# -----------------------------------------
print("\n📌 Fetching ERC20 Token Transfers...")

token_params = {
    "chainid": CHAIN_ID,
    "module": "account",
    "action": "tokentx",
    "address": TARGET_WALLET,
    "page": 1,
    "offset": 20,
    "sort": "desc",
    "apikey": API_KEY
}

token_response = requests.get(BASE_URL, params=token_params)
token_data = token_response.json()

if token_data["status"] == "1":
    print("✅ Token Transfers Found:", len(token_data["result"]))

    with open("wallet_token_transfers.json", "w") as f:
        json.dump(token_data, f, indent=4)

else:
    print("⚠️ Token transfer fetch failed!")


# -----------------------------------------
# 5. OPEN ETHERSCAN PAGE
# -----------------------------------------
print("\n🚀 Opening Full Wallet Data in Browser...")

etherscan_url = f"https://etherscan.io/address/{TARGET_WALLET}"
webbrowser.open(etherscan_url)

print("\n✅ FORENSIC SCAN COMPLETE!")
print("📂 JSON Files Saved in Your Project Folder.")
