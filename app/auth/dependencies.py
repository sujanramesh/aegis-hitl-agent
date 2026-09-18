from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.auth.models import User, UserRole
from app.auth.security import decode_access_token


# =========================================================
# OAuth2 bearer-token extraction
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)


# =========================================================
# Authentication dependency
# =========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Validate the supplied bearer token and return the
    authenticated Aegis user identity.

    Invalid or expired tokens are rejected with HTTP 401.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = decode_access_token(token)

    except (
        InvalidTokenError,
        ValueError,
    ):
        raise credentials_exception

    if not payload.sub:
        raise credentials_exception

    return User(
        username=payload.sub,
        role=payload.role,
    )


# =========================================================
# Role authorization dependency
# =========================================================

def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    """
    Create a FastAPI dependency that permits access only
    to authenticated users with one of the allowed roles.
    """

    def role_checker(
        current_user: User = Depends(
            get_current_user
        ),
    ) -> User:

        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled.",
            )

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this action."
                ),
            )

        return current_user

    return role_checker