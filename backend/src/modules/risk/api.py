from fastapi import FastAPI
from risk_engine import risk_engine
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="🚨 Blockchain Forensics API")

class WalletInput(BaseModel):
    address: str
    balance: float = 0
    total_transactions: int = 0
    incoming_amounts: list = []
    outgoing_amounts: list = []
    tx_timestamps: list = []
    cluster_size: int = 1
    avg_degree: float = 0
    days_inactive: int = 0
    post_reactivation_tx_per_day: float = 0

@app.post("/analyze")
async def analyze_wallet(wallet: WalletInput):
    result = risk_engine(wallet.dict())
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
