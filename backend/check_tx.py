import os
import pymongo
from dotenv import load_dotenv

env_path = "c:/Users/saksh/OneDrive/Desktop/unified/Unified-Dashboard/backend/.env"
load_dotenv(env_path)

from src.config.settings import settings

client = pymongo.MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]

print("Total transactions:", db["revenue_transactions"].count_documents({}))

txs = list(db["revenue_transactions"].find().limit(30))
for idx, tx in enumerate(txs):
    print(f"{idx}: id={tx.get('external_transaction_id')}, product={tx.get('product_code')}, provider={tx.get('provider')}, platform={tx.get('platform')}, status={tx.get('status')}, date={tx.get('transaction_date')}, amount={tx.get('gross_amount')}")
