from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.utils.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_verifies_without_storing_plaintext():
    password = "PaperTrade123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("incorrect-password", hashed)


def test_access_and_refresh_tokens_are_type_scoped():
    user_id = uuid4()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    assert decode_token(access_token, expected_type="access") == user_id
    assert decode_token(refresh_token, expected_type="refresh") == user_id

    with pytest.raises(InvalidTokenError):
        decode_token(refresh_token, expected_type="access")


def test_invalid_token_is_rejected():
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-jwt")


def test_production_requires_long_random_secrets():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENV="production",
            SECRET_KEY="too-short",
            JWT_SECRET="also-too-short",
            MARKET_MODE="demo",
        )
