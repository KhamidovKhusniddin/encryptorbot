import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 32-byte key from password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt_data_with_password(data: bytes, password: str) -> tuple[bytes, bytes, bytes]:
    """
    Encrypts data (e.g. keys) using a derived key from password.
    Returns (salt, iv, ciphertext).
    """
    salt = os.urandom(16)
    key = derive_key(password, salt)
    
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return salt, iv, ciphertext

def decrypt_data_with_password(salt: bytes, iv: bytes, ciphertext: bytes, password: str) -> bytes:
    """
    Decrypts data using derived key from password.
    """
    key = derive_key(password, salt)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data
