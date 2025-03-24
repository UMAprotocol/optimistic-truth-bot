from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)
db = client["testdatabase"]
collection = db["testcollection"]

# Read one document
doc = collection.find_one()
print("Read:", doc)

# Insert one document
result = collection.insert_one({"name": "Alice", "age": 30})
print("Inserted ID:", result.inserted_id)