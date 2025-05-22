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
    print("🛑 Disconnected from MongoDB.")

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
    users_collection = app.mongodb_db["users"] # Access the users collection

    # Find the user in MongoDB
    db_user = await users_collection.find_one({"email": user.email})

    if db_user and db_user["password"] == user.password:
        token = jwt.encode({"email": user.email, "role": db_user["role"]}, SECRET_KEY, algorithm=ALGORITHM)
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


@app.post("/api/login_safe")
async def login(user: UserLogin):
    print(f"\n--- Attempting login for email: {user.email} ---")
    users_collection = app.mongodb_db["users"]

    try:
        db_user = await users_collection.find_one({"email": user.email})
        print(f"DB user found: {db_user}")

        if not db_user:
            print("User not found!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password" 
            )

        if db_user["password"] == user.password:
            print("Password match!")
            token_payload = {"email": db_user["email"], "role": db_user.get("role", "user")}
            token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
            return {"message": "Login successful", "token": token}
        else:
            print("Password mismatch!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/login")
async def vuln_login(payload: dict):
    print(f"Payload: {payload}")
    email = payload.get("email")
    password = payload.get("password")

    users_collection = app.mongodb_db["users"]

    try:
        db_user = await users_collection.find_one({"email": email, "password": password})
        print(f"User found: {db_user}")

        if db_user:
            token = jwt.encode({"email": db_user["email"], "role": db_user["role"]}, SECRET_KEY, algorithm=ALGORITHM)
            return {"message": "Login successful", "token": token}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


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

