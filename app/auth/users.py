import os

from dotenv import load_dotenv

from app.auth.models import UserInDB
from app.auth.security import hash_password


# =========================================================
# Configuration
# =========================================================

load_dotenv()


# =========================================================
# Development users
# =========================================================

def _load_development_users() -> dict[str, UserInDB]:
    """
    Build the development user store from passwords
    supplied through environment variables.

    Plaintext passwords are never stored in the user
    objects themselves.
    """

    viewer_password = os.getenv(
        "AEGIS_VIEWER_PASSWORD"
    )

    operator_password = os.getenv(
        "AEGIS_OPERATOR_PASSWORD"
    )

    approver_password = os.getenv(
        "AEGIS_APPROVER_PASSWORD"
    )

    if not all([
        viewer_password,
        operator_password,
        approver_password,
    ]):
        raise ValueError(
            "Aegis development user passwords "
            "are not fully configured."
        )

    return {
        "viewer": UserInDB(
            username="viewer",
            role="viewer",
            hashed_password=hash_password(
                viewer_password
            ),
        ),
        "operator": UserInDB(
            username="operator",
            role="operator",
            hashed_password=hash_password(
                operator_password
            ),
        ),
        "approver": UserInDB(
            username="approver",
            role="approver",
            hashed_password=hash_password(
                approver_password
            ),
        ),
    }


USERS = _load_development_users()


# =========================================================
# User lookup
# =========================================================

def get_user(
    username: str,
) -> UserInDB | None:
    """
    Retrieve an Aegis user by username.
    """

    return USERS.get(username)