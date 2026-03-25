from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Соль для KDF — должна быть постоянной и храниться отдельно
SALT = b"\x13\x9f\x8a\x7c\x2d\x1e\x9b\x4f\xaa\xcd\x88\xef\x10\x2a\x3c\x5d"


def password_to_fernet_key(password: str) -> bytes:
    """Преобразует пароль в ключ Fernet с помощью PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100_000,
        backend=default_backend(),
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_env_file(
    password: str, env_path: str = ".env", encrypted_path: str = ".env.enc"
):
    """Шифрует .env файл и сохраняет его как .env.enc"""
    key = password_to_fernet_key(password)
    fernet = Fernet(key)

    with open(env_path, "rb") as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(encrypted_path, "wb") as f:
        f.write(encrypted)


def load_env_with_password(password: str, encrypted_path: str = ".env.enc") -> dict:
    """Расшифровывает .env.enc и возвращает переменные окружения как словарь"""
    key = password_to_fernet_key(password)
    fernet = Fernet(key)

    with open(encrypted_path, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = fernet.decrypt(encrypted_data).decode()

    # Преобразуем расшифрованный текст в словарь переменных окружения
    env_vars = dict(
        line.split("=", 1)
        for line in decrypted_data.splitlines()
        if "=" in line and not line.strip().startswith("#")
    )

    return env_vars

