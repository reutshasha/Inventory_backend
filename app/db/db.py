from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client["users_db"]

async def init_db_mongodb(): 
    users_collection = db["users"]

    await users_collection.delete_many({})
    users_to_insert = [
        {'email': 'admin@example.com', 'password': '123456', 'role': 'admin'},
        {'email': 'user@example.com', 'password': 'password', 'role': 'user'}
    ]
    await users_collection.insert_many(users_to_insert)
    
    print("✅ MongoDB initialized with user data.")



# from motor.motor_asyncio import AsyncIOMotorClient
# import asyncio 

# MONGO_URL = "mongodb://localhost:27017"
# client = AsyncIOMotorClient(MONGO_URL)
# db = client["users_db"] 

# async def init_db_mongodb(): 
#     users_collection = db["users"] 

#     await users_collection.delete_many({})

#     users_to_insert = [
#         {'email': 'admin@example.com', 'password': '123456', 'role': 'admin'},
#         {'email': 'user@example.com', 'password': 'password', 'role': 'user'}
#     ]
#     await users_collection.insert_many(users_to_insert)
#     print("MongoDB initialized with user data.")

# async def run_init_db_mongodb():
#     await init_db_mongodb()
#     client.close()

# if __name__ == "__main__":
#     asyncio.run(run_init_db_mongodb())




# MONGO_URL = "mongodb://localhost:27017"
# client = AsyncIOMotorClient(MONGO_URL)
# db = client["users_db"]  








# def init_db():
#     conn = sqlite3.connect("demo.db")
#     cursor = conn.cursor()
#     cursor.execute("DROP TABLE IF EXISTS users")
#     cursor.execute("CREATE TABLE users (email TEXT, password TEXT, role TEXT)")
#     cursor.execute("INSERT INTO users VALUES ('admin@example.com', '123456', 'admin')")
#     cursor.execute("INSERT INTO users VALUES ('user@example.com', 'password', 'user')")
#     conn.commit()
#     conn.close()