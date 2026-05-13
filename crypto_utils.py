"""
crypto_utils.py — AES-256 encryption/decryption with PBKDF2 key derivation
"""

import os
import base64
import hashlib
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


SALT_LENGTH = 16
NONCE_LENGTH = 12
ITERATIONS = 200_000
KEY_LENGTH = 32  # 256-bit


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive AES-256 key from password using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_data(data: bytes, password: str) -> bytes:
    """
    Encrypt data using AES-256-GCM.
    Format: [SALT (16 bytes)] + [NONCE (12 bytes)] + [CIPHERTEXT + TAG]
    """
    salt = os.urandom(SALT_LENGTH)
    nonce = os.urandom(NONCE_LENGTH)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)  # No AAD

    return salt + nonce + ciphertext


def decrypt_data(encrypted: bytes, password: str):
    """
    Decrypt AES-256-GCM encrypted data.
    Returns decrypted bytes or None on failure.
    """
    if len(encrypted) < SALT_LENGTH + NONCE_LENGTH + 16:
        return None

    try:
        salt = encrypted[:SALT_LENGTH]
        nonce = encrypted[SALT_LENGTH:SALT_LENGTH + NONCE_LENGTH]
        ciphertext = encrypted[SALT_LENGTH + NONCE_LENGTH:]

        key = derive_key(password, salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        return None


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file on disk."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
