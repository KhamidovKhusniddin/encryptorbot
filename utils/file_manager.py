import os
import zipfile
import base64
from typing import Dict
try:
    import pyzipper
except ImportError:
    pyzipper = None

def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def write_file(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)

def delete_file(path: str):
    if os.path.exists(path):
        os.remove(path)

def create_secure_zip(
    zip_path: str,
    encrypted_file_path: str,
    key_data: bytes,
    meta_data: Dict[str, bytes] = None,
    password: str = None
):
    """
    Creates a secure zip.
    If 'password' is provided and pyzipper is available, 
    the ZIP itself will be AES-encoded with that password.
    """
    # Prefer pyzipper for AES encryption if password is provided
    if password and pyzipper:
        with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode())
            _write_zip_contents(zf, encrypted_file_path, key_data, meta_data)
    else:
        # Fallback to standard zip (no password on zip itself, or legacy if we tried)
        # Note: Standard zipfile supports password but only legacy weak encryption.
        # We stick to no-zip-password if pyzipper missing, trusting our inner encryption.
        with zipfile.ZipFile(zip_path, 'w') as zf:
             # if password: zf.setpassword(password.encode()) # Legacy only, skip for now to avoid confusion
            _write_zip_contents(zf, encrypted_file_path, key_data, meta_data)

def _write_zip_contents(zf, encrypted_file_path, key_data, meta_data):
    # Add the encrypted file
    zf.write(encrypted_file_path, os.path.basename(encrypted_file_path))
    
    # Add the key file (Base64)
    if isinstance(key_data, bytes):
        key_b64 = base64.b64encode(key_data).decode('utf-8')
        zf.writestr("key.txt", key_b64)
    else:
        # If key_data is already processed/ignored
        pass
    
    # Add metadata
    if meta_data:
        for name, content in meta_data.items():
            if isinstance(content, bytes):
                content_b64 = base64.b64encode(content).decode('utf-8')
                zf.writestr(f"{name}.txt", content_b64)
            else:
                zf.writestr(f"{name}.txt", str(content))

def extract_secure_zip(zip_path: str, extract_to: str, password: str = None) -> Dict[str, str]:
    """
    Extracts the secure zip.
    """
    # Detect if pyzipper needed
    try:
        # Try standard first (or if it's not encrypted)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check if encrypted usage
            is_encrypted = False
            for info in zf.infolist():
                if info.flag_bits & 0x1:
                    is_encrypted = True
                    break
            
            if not is_encrypted:
                zf.extractall(extract_to)
                return {name: os.path.join(extract_to, name) for name in zf.namelist()}
    except:
        pass # Might fail if AES encrypted and zipfile can't handle it

    # Try pyzipper
    if pyzipper:
        try:
            with pyzipper.AESZipFile(zip_path, 'r') as zf:
                if password:
                    zf.setpassword(password.encode())
                zf.extractall(extract_to)
                return {name: os.path.join(extract_to, name) for name in zf.namelist()}
        except RuntimeError as e:
            if 'Bad password' in str(e) or 'password required' in str(e):
                raise ValueError("ZIP password needed or incorrect")
            raise e
    
    # Fallback to standard for legacy password
    with zipfile.ZipFile(zip_path, 'r') as zf:
        if password:
            zf.setpassword(password.encode())
        zf.extractall(extract_to)
        return {name: os.path.join(extract_to, name) for name in zf.namelist()}
