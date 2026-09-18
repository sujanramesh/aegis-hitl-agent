import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.auth.models import TokenPayload


# =========================================================
# Configuration
# =========================================================

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30",
    )
)

if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY is not configured"
    )


# =========================================================
# Password hashing
# =========================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Securely hash a plaintext password using the
    recommended password-hashing configuration.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plaintext password against its stored hash.
    """

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# =========================================================
# JWT creation
# =========================================================

def create_access_token(
    username: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT representing an authenticated
    Aegis user.
    """

    if not username:
        raise ValueError(
            "Username cannot be empty."
        )

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expires_at = now + expires_delta

    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# =========================================================
# JWT validation
# =========================================================

def decode_access_token(
    token: str,
) -> TokenPayload:
    """
    Validate and decode an Aegis access token.

    Invalid, malformed, expired, or otherwise unverifiable
    tokens are rejected.
    """

    if not token:
        raise InvalidTokenError(
            "Access token is empty."
        )

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )

    return TokenPayload(
        sub=payload.get("sub"),
        role=payload.get("role"),
    )