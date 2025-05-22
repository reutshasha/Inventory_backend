from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests 
from .models import UserLogin
# from app.db.db import db 
from app.db.db import init_db_mongodb, client as mongo_client
from bson.objectid import ObjectId
import jwt



# סוד אמיתי אמור להיות מורכב. כאן נשתמש בסוד פומבי (פגיע)
SECRET_KEY = "insecure-secret"
ALGORITHM = "HS256"

# יצירת מודל פשוט למידע התחברות
# class UserLogin(BaseModel):
#     email: str
#     password: str
#     # ssrf
# class URLRequest(BaseModel):
#     url: str

# טבלת משתמשים פיקטיבית (למטרת ההדגמה)
# users_db = {
#     "admin@example.com": {"password": "123456", "role": "admin"},
#     "user@example.com": {"password": "password", "role": "user"},
# }

app = FastAPI(
    title="Inventory Management Demo",
    description="Demo app with OWASP Top 10 vulnerabilities",
    version="0.1"
)
    
@app.on_event("startup")
async def startup_event():
    app.mongodb_client = mongo_client
    app.mongodb_db = app.mongodb_client["users_db"]
    await init_db_mongodb()

@app.on_event("shutdown")
async def shutdown_event():
    # סוגר את חיבור ה-MongoDB כשהאפליקציה נכבית
    app.mongodb_client.close()
    print("FastAPI application shutdown. MongoDB connection closed.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# פונקציה ליצירת טוקן
@app.post("/api/token")
async def create_token(user: UserLogin):
    print("UserLogin!")

    if user.email in users_db and users_db[user.email]["password"] == user.password:
        token = jwt.encode({"email": user.email, "role": users_db[user.email]["role"]}, SECRET_KEY, algorithm=ALGORITHM)
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# TODO:CHECK
@app.get("/api/vuln-data")
async def get_sensitive_data(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    try:
        # : לא בודקים חתימה!
        payload = jwt.decode(token, options={"verify_signature": False})
        return {"message": f"Hello {payload['email']}, your role is {payload['role']}"}
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid token")


# Endpoint של התחברות
# @app.post("/api/login")
# async def login(user: UserLogin):
#     # כאן נעשה את כל ההתחברות הפגומה
#     # POC של SQL Injection
#     if user.email in users_db and users_db[user.email]["password"] == user.password:
#         return {"message": "Login successful", "role": users_db[user.email]["role"]}
#     raise HTTPException(status_code=401, detail="Invalid credentials")



@app.post("/api/vuln-login")
async def vuln_login(user: UserLogin):
    try:

        email = user.email
        password = user.password

        users_collection = app.mongodb_db["users"]

        print("Email:", email)
        print("Password:", password)
        print("Users collection (MotorCollection object):", users_collection)

        user_in_db = await users_collection.find_one({"email": email})
        print(f"User found in DB: {user_in_db}")

        if user_in_db:
            if password == "' OR '1'='1'":
                response = JSONResponse(content={"message": "Login successful (bypassed with SQL Injection!)"})
                response.set_cookie(key="session_id", value="injected_admin_token", httponly=True)
                return response
            elif user_in_db.get("password") == password:
                response = JSONResponse(content={"message": "Login successful"})
                response.set_cookie(key="session_id", value="regular_user_token", httponly=True)
                return response

        raise HTTPException(status_code=401, detail="Invalid credentials") 

    except Exception as e:
        print(f"ERROR in /api/vuln-login: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred. Check server logs for details.")
    
# # TODO:FIX!
# @app.post("/api/vuln-login")
# async def vuln_login(user: UserLogin):
#     email = user.email
#     password = user.password

#     users_collection = app.mongodb["users"] 

#     # שאילתת MongoDB נכונה לחיפוש משתמש
#     user_in_db = await users_collection.find_one({"email": email})
#     print(f"User found in DB: {user_in_db}")

# TODO:query injection in mongoDB 
    # queryEmail = db.users_db.find({ email: user.email, password: user.password })
    # collection = db["users_db"]

    # user_in_db = await collection.find_one({"email": user.email, "password": user.password})

    # print(user_in_db)


    # user_in_db = await collection.find_one({"email": email})
    # user_in_db = await collection.find_one(queryEmail)
    # print(user_in_db)
    # if password == "' OR '1'='1":
    #     return {"message": "Login successful (injection bypass)", "role": "admin"}
    
    # if not user_in_db:
    #     raise HTTPException(status_code=401, detail="User not found")

    # if user_in_db["password"] != password:
    #     raise HTTPException(status_code=401, detail="Wrong password")

    # return {"message": "Login successful", "role": user_in_db["role"]}


# XSS Vulnerable endpoint
comments = []

@app.post("/xss/store-comment", response_class=HTMLResponse)
async def store_comment(comment: str = Form(...)):
    comments.append(comment)
    return HTMLResponse(
        f"""
        <p>Comment stored!</p>
        <a href="/xss/store-comment">View all comments</a>
        """
    )
# @app.post("/xss/store-comment")
# async def store_comment(comment: str = Form(...)):
#     comments.append(comment)
#     return {"message": "Comment stored"}

@app.get("/api/xss/comment", response_class=HTMLResponse)
async def vuln_comment(your_comment: str):
    # ❗ אין סניטיזציה – פשוט מחזיר HTML עם הקלט של המשתמש
    html_content = f"""
    <html>
        <body>
            <h3>Your comment:</h3>
            <div>{your_comment}</div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


# SSRF Vulnerable endpoint
@app.post("/api/ssrf")
# async def ssrf_vulnerable(payload: URLRequest):
#     try:
#         # ❗ השרת מבצע קריאה לאמת ה-URL מבלי לסנן אותו
#         response = requests.get(payload.url)
#         return {"status_code": response.status_code, "content": response.text[:200]}  # מגבילים את התוכן לחלק ממנו
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#   @app.post("/api/ssrf")
# async def ssrf_vulnerable(payload: URLRequest):
#     try:
#         # ❗ השרת מבצע קריאה לכתובת ה-URL מבלי לסנן אותה
#         response = requests.get(payload.url, timeout=5)  # הוספת timeout
#         # limit the amount of content we return to the user.
#         return {"status_code": response.status_code, "content": response.text[:200]}
#     except requests.exceptions.Timeout:
#         return {"status_code": 500, "detail": "Request timed out"}
#     except Exception as e:
#         return {"status_code": 500, "detail": str(e)}
# SSRF Vulnerable endpoint
# async def ssrf_vulnerable(payload: URLRequest):
#     try:
#         # ❗ השרת מבצע קריאה לכתובת ה-URL מבלי לסנן אותה
#         # Use httpx instead of requests, and set a short timeout
#         async with httpx.AsyncClient() as client:
#             response = await client.get(payload.url, timeout=5)
#         response.raise_for_status()  # Raise an exception for bad status codes

#         # limit the amount of content we return to the user.
#         return {"status_code": response.status_code, "content": response.text[:200]}
#     except httpx.TimeoutException:
#         return {"status_code": 500, "detail": "Request timed out"}
#     except httpx.RequestError as e:
#         return {"status_code": 500, "detail": f"Request error: {str(e)}"}
#     except Exception as e:
#         return {"status_code": 500, "detail": f"An error occurred: {str(e)}"}
@app.get("/")
def read_root():
    return {"message": "App is running"}

