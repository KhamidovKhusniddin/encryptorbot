import unittest
import os
import shutil
import base64
from encryption import aes_cipher, rsa_cipher, ecc_cipher
from utils import file_manager

class TestEncryption(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_file_path = os.path.join(self.test_dir, "test.txt")
        self.test_data = b"Hello World! This is a secret message."
        with open(self.test_file_path, "wb") as f:
            f.write(self.test_data)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_aes(self):
        key = aes_cipher.generate_aes_key()
        iv, ciphertext = aes_cipher.encrypt_aes(self.test_data, key)
        plaintext = aes_cipher.decrypt_aes(iv, ciphertext, key)
        self.assertEqual(self.test_data, plaintext)

    def test_rsa_hybrid(self):
        # 1. Keys
        priv, pub = rsa_cipher.generate_rsa_key_pair()
        
        # 2. Encrypt AES Key
        aes_key = aes_cipher.generate_aes_key()
        enc_aes_key = rsa_cipher.encrypt_rsa(aes_key, pub)
        
        # 3. Decrypt AES Key
        dec_aes_key = rsa_cipher.decrypt_rsa(enc_aes_key, priv)
        self.assertEqual(aes_key, dec_aes_key)
        
        # 4. Encrypt Data with AES
        iv, ciphertext = aes_cipher.encrypt_aes(self.test_data, aes_key)
        
        # 5. Decrypt Data
        plaintext = aes_cipher.decrypt_aes(iv, ciphertext, dec_aes_key)
        self.assertEqual(self.test_data, plaintext)

    def test_ecc_hybrid(self):
        # 1. Keys
        priv, pub = ecc_cipher.generate_ecc_key_pair()
        
        # 2. Encrypt AES Key
        aes_key = aes_cipher.generate_aes_key()
        ephem_pub_bytes, iv, ciphertext = ecc_cipher.encrypt_ecc_hybrid(aes_key, pub)
        
        # 3. Decrypt AES Key
        dec_aes_key = ecc_cipher.decrypt_ecc_hybrid(ephem_pub_bytes, iv, ciphertext, priv)
        self.assertEqual(aes_key, dec_aes_key)

    def test_zip_utils(self):
        zip_path = os.path.join(self.test_dir, "test.zip")
        file_manager.create_secure_zip(
            zip_path, 
            self.test_file_path, 
            b"fake_key_123", 
            {"extra": "info"}
        )
        self.assertTrue(os.path.exists(zip_path))
        
        extract_dir = os.path.join(self.test_dir, "extracted")
        extracted = file_manager.extract_secure_zip(zip_path, extract_dir)
        self.assertIn("key.txt", extracted)
        self.assertIn("extra.txt", extracted)

if __name__ == "__main__":
    unittest.main()
