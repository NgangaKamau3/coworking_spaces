from cryptography.fernet import Fernet
from django.conf import settings
from base64 import urlsafe_b64encode

class FieldEncryption:
    def __init__(self):
        key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(urlsafe_b64encode(key[:32]))
    
    def encrypt(self, data: str) -> str:
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

encryption = FieldEncryption()