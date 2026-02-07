import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
import dotenv

dotenv.load_dotenv()

# Primary key source for token encryption/decryption.
CRYPTO_SECRET_KEY = (os.getenv("CRYPTO_SECRET_KEY") or "").strip()


def _derive_fernet_key(raw_secret: str) -> bytes:
    """
    Derive a valid Fernet key from any secret text.
    Fernet expects urlsafe_b64(32-byte-key).
    """
    digest = hashlib.sha256((raw_secret or "").encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _build_fernet() -> Fernet:
    if CRYPTO_SECRET_KEY:
        try:
            # If already a valid Fernet key, use directly.
            return Fernet(CRYPTO_SECRET_KEY.encode("utf-8"))
        except Exception:
            # Treat non-Fernet values as passphrase and derive key.
            return Fernet(_derive_fernet_key(CRYPTO_SECRET_KEY))

    # CI/dev fallback so imports never crash when env is missing.
    fallback_secret = (
        os.getenv("DJANGO_SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or getattr(settings, "SECRET_KEY", "")
        or "frontliner-local-fallback-secret"
    )
    return Fernet(_derive_fernet_key(fallback_secret))


fernet = _build_fernet()

def encrypt_token(token: str = None) -> str:
    if not token:
        return None
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    if not encrypted_token:
        return None

    try:
        return fernet.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        return None
