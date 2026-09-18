from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import require_roles
from app.auth.models import User
from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# =========================================================
# Test application
# =========================================================

auth_test_app = FastAPI()


@auth_test_app.get("/viewer-area")
def viewer_area(
    current_user: User = Depends(
        require_roles(
            "viewer",
            "operator",
            "approver",
        )
    ),
):
    return {
        "username": current_user.username,
        "role": current_user.role,
    }


@auth_test_app.post("/operator-area")
def operator_area(
    current_user: User = Depends(
        require_roles(
            "operator",
            "approver",
        )
    ),
):
    return {
        "username": current_user.username,
        "role": current_user.role,
    }


@auth_test_app.post("/approver-area")
def approver_area(
    current_user: User = Depends(
        require_roles(
            "approver",
        )
    ),
):
    return {
        "username": current_user.username,
        "role": current_user.role,
    }


client = TestClient(auth_test_app)


# =========================================================
# Helpers
# =========================================================

def authorization_header(
    username: str,
    role: str,
) -> dict[str, str]:

    token = create_access_token(
        username=username,
        role=role,
    )

    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


# =========================================================
# Password security
# =========================================================

def test_password_hashing_and_verification():

    password = "SecurePassword123!"

    hashed = hash_password(
        password
    )

    assert hashed != password

    assert verify_password(
        password,
        hashed,
    )

    assert not verify_password(
        "WrongPassword",
        hashed,
    )


# =========================================================
# JWT security
# =========================================================

def test_access_token_contains_identity_and_role():

    token = create_access_token(
        username="alice",
        role="approver",
    )

    payload = decode_access_token(
        token
    )

    assert payload.sub == "alice"
    assert payload.role == "approver"


def test_expired_access_token_is_rejected():

    token = create_access_token(
        username="alice",
        role="viewer",
        expires_delta=timedelta(
            seconds=-1
        ),
    )

    with pytest.raises(Exception):
        decode_access_token(
            token
        )


# =========================================================
# Authentication boundary
# =========================================================

def test_protected_endpoint_rejects_missing_token():

    response = client.get(
        "/viewer-area"
    )

    assert response.status_code == 401


# =========================================================
# Viewer permissions
# =========================================================

def test_viewer_can_access_read_only_area():

    response = client.get(
        "/viewer-area",
        headers=authorization_header(
            username="viewer-user",
            role="viewer",
        ),
    )

    assert response.status_code == 200

    assert response.json()["role"] == (
        "viewer"
    )


def test_viewer_cannot_access_operator_area():

    response = client.post(
        "/operator-area",
        headers=authorization_header(
            username="viewer-user",
            role="viewer",
        ),
    )

    assert response.status_code == 403


def test_viewer_cannot_access_approver_area():

    response = client.post(
        "/approver-area",
        headers=authorization_header(
            username="viewer-user",
            role="viewer",
        ),
    )

    assert response.status_code == 403


# =========================================================
# Operator permissions
# =========================================================

def test_operator_can_access_viewer_area():

    response = client.get(
        "/viewer-area",
        headers=authorization_header(
            username="operator-user",
            role="operator",
        ),
    )

    assert response.status_code == 200


def test_operator_can_access_operator_area():

    response = client.post(
        "/operator-area",
        headers=authorization_header(
            username="operator-user",
            role="operator",
        ),
    )

    assert response.status_code == 200


def test_operator_cannot_access_approver_area():

    response = client.post(
        "/approver-area",
        headers=authorization_header(
            username="operator-user",
            role="operator",
        ),
    )

    assert response.status_code == 403


# =========================================================
# Approver permissions
# =========================================================

def test_approver_can_access_viewer_area():

    response = client.get(
        "/viewer-area",
        headers=authorization_header(
            username="approver-user",
            role="approver",
        ),
    )

    assert response.status_code == 200


def test_approver_can_access_operator_area():

    response = client.post(
        "/operator-area",
        headers=authorization_header(
            username="approver-user",
            role="approver",
        ),
    )

    assert response.status_code == 200


def test_approver_can_access_approver_area():

    response = client.post(
        "/approver-area",
        headers=authorization_header(
            username="approver-user",
            role="approver",
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["username"] == (
        "approver-user"
    )

    assert body["role"] == (
        "approver"
    )