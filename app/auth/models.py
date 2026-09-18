from typing import Literal

from pydantic import BaseModel


# =========================================================
# Supported authorization roles
# =========================================================

UserRole = Literal[
    "viewer",
    "operator",
    "approver",
]


# =========================================================
# User models
# =========================================================

class User(BaseModel):
    """
    Public representation of an authenticated Aegis user.

    Passwords and password hashes must never be included
    in this model.
    """

    username: str
    role: UserRole
    disabled: bool = False


class UserInDB(User):
    """
    Internal representation of a user containing the
    password hash required during authentication.
    """

    hashed_password: str


# =========================================================
# Authentication request/response models
# =========================================================

class Token(BaseModel):
    """
    JWT access-token response returned after successful
    authentication.
    """

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Claims extracted and validated from an Aegis JWT.
    """

    sub: str
    role: UserRole