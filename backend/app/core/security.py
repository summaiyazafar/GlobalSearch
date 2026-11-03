import hashlib
import hmac
import secrets
from uuid import uuid4


def generate_request_id() -> str:
    return str(uuid4())


def generate_secure_token(length: int = 32) -> str:
    if length < 16:
        raise ValueError("Token length must be at least 16 bytes")

    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    calculated_hash = hash_token(token)
    return hmac.compare_digest(calculated_hash, token_hash)
