import pyzipper
import os

print("Testing ZIP Encryption...")
with pyzipper.AESZipFile('test_secure.zip', 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
    zf.setpassword(b"123")
    zf.writestr("test.txt", "Secret Content")

print("Created test_secure.zip with password '123'.")
print("Trying to read without password...")

try:
    with pyzipper.AESZipFile('test_secure.zip', 'r') as zf:
        zf.read("test.txt")
    print("FAIL: Read without password!")
except RuntimeError:
    print("SUCCESS: Password required caught.")
except Exception as e:
    print(f"SUCCESS: Other error caught: {e}")
