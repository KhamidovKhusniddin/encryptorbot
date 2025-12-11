import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

def generate_aes_key():
    """Generates a random 256-bit AES key."""
    return os.urandom(32)

def encrypt_aes(data: bytes, key: bytes) -> tuple[bytes, bytes]:
    """
    Encrypts data using AES-256-CBC.
    Returns (iv, ciphertext).
    """
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv, ciphertext

def decrypt_aes(iv: bytes, ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypts data using AES-256-CBC.
    """
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data
