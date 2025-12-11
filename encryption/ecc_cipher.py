from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def generate_ecc_key_pair():
    """Generates an ECC key pair (SECP256R1)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

def encrypt_ecc_hybrid(data: bytes, public_key) -> tuple[bytes, bytes, bytes]:
    """
    Encrypts data using ECC Hybrid approach (ECIES-like).
    1. Generate ephemeral key pair.
    2. Perform ECDH to get shared secret.
    3. Derive Key from shared secret.
    4. Encrypt data with derived key (AES-GCM).
    Returns (ephemeral_public_key_bytes, iv, ciphertext).
    Note: Standard ECC doesn't encrypt directly like RSA. It relies on Key Exchange.
    Here 'data' is typically the AES Key we want to protect.
    """
    # 1. Ephemeral key
    ephemeral_private = ec.generate_private_key(ec.SECP256R1())
    ephemeral_public = ephemeral_private.public_key()
    
    # 2. Shared secret
    shared_key = ephemeral_private.exchange(ec.ECDH(), public_key)
    
    # 3. Derive key
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'ECC_HYBRID_ENCRYPTION',
    ).derive(shared_key)
    
    # 4. Encrypt data
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    
    ephemeral_pub_bytes = ephemeral_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return ephemeral_pub_bytes, iv, ciphertext + encryptor.tag

def decrypt_ecc_hybrid(ephemeral_pub_bytes: bytes, iv: bytes, ciphertext_with_tag: bytes, private_key) -> bytes:
    """
    Decrypts data using ECC private key.
    """
    # Load ephemeral public key
    ephemeral_public = serialization.load_pem_public_key(ephemeral_pub_bytes, backend=default_backend())
    
    # ECDH
    shared_key = private_key.exchange(ec.ECDH(), ephemeral_public)
    
    # Derive key
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'ECC_HYBRID_ENCRYPTION',
    ).derive(shared_key)
    
    # Decrypt
    tag = ciphertext_with_tag[-16:]
    actual_ciphertext = ciphertext_with_tag[:-16]
    
    cipher = Cipher(algorithms.AES(derived_key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    data = decryptor.update(actual_ciphertext) + decryptor.finalize()
    
    return data
