# backend/app/security/auth.py
from jose import jwt

SECRET_KEY = "secret"  # ❌ חלש, לא מאובטח
ALGORITHM = "HS256"

def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
