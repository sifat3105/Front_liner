from cryptography.fernet import Fernet
import dotenv
import os

dotenv.load_dotenv()

SECRET_KEY = os.getenv("CRYPTO_SECRET_KEY")


fernet = Fernet(SECRET_KEY.encode())

def encrypt_token(token: str = None) -> str:
    if not token:
        return None
    return fernet.encrypt(token.encode()).decode()

from cryptography.fernet import InvalidToken

def decrypt_token(encrypted_token):
    if not encrypted_token:
        return None

    try:
        return fernet.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        return None
