from cryptography.fernet import Fernet
from django.conf import settings
import base64

class FieldEncryption:
    def __init__(self):
        key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(base64.urlsafe_b64encode(key[:32]))
    
    def encrypt(self, data: str) -> str:
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

encryption = FieldEncryption()