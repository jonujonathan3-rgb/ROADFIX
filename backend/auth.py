
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Load private credentials from backend/.env
load_dotenv(Path(__file__).with_name(".env"))

ADMIN_USERNAME = os.getenv("ROADFIX_ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ROADFIX_ADMIN_PASSWORD")
SECRET_KEY = os.getenv("ROADFIX_SECRET_KEY")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def verify_admin_credentials(username: str, password: str) -> bool:
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return False

    return (
        secrets.compare_digest(username, ADMIN_USERNAME)
        and secrets.compare_digest(password, ADMIN_PASSWORD)
    )


def create_access_token(username: str) -> str:
    if not SECRET_KEY:
        raise RuntimeError("ROADFIX_SECRET_KEY is not configured.")

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expires_at,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired admin login. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not SECRET_KEY or not ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication is not configured.",
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username = payload.get("sub")

        if not isinstance(username, str) or not secrets.compare_digest(
            username, ADMIN_USERNAME
        ):
            raise unauthorized

        return username

    except JWTError:
        raise unauthorized