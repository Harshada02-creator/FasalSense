import os, time, json, hmac, hashlib, base64
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET = os.getenv("SECRET_KEY", "dev-only-change-this-secret-before-deploying")
bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_s, digest_s = stored.split("$", 1)
        salt, expected = base64.b64decode(salt_s), base64.b64decode(digest_s)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 240_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def create_token(user: User) -> str:
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    payload = _b64(json.dumps({"sub":user.id,"role":user.role,"exp":int(time.time()) + 60*60*24*7}).encode())
    body = header + "." + payload
    sig = _b64(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return body + "." + sig

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(401, "Please log in to continue.")
    try:
        head, payload, signature = credentials.credentials.split(".")
        body = head + "." + payload
        expected = _b64(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if claims["exp"] < int(time.time()):
            raise ValueError("expired")
        user = db.get(User, int(claims["sub"]))
        if not user:
            raise ValueError("user")
        return user
    except Exception:
        raise HTTPException(401, "Session is invalid or expired. Please log in again.")

def get_optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    if not credentials or not credentials.credentials:
        return None
    try:
        head, payload, signature = credentials.credentials.split(".")
        body = head + "." + payload
        expected = _b64(hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if claims["exp"] < int(time.time()):
            return None
        user = db.get(User, int(claims["sub"]))
        return user
    except Exception:
        return None

def require_role(*roles):
    def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Your account does not have permission for this action.")
        return user
    return dependency
