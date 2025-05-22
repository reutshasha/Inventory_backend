import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db 
import asyncio

users_db = {
    "admin@example.com": {"password": "123456", "role": "admin"},
    "user@example.com": {"password": "password", "role": "user"},
}

async def create_users():
    collection = db["users"]
    await collection.delete_many({})
    for email, data in users_db.items():
        await collection.insert_one({
            "email": email,
            "password": data["password"],
            "role": data["role"]
        })

if __name__ == "__main__":
    asyncio.run(create_users())
