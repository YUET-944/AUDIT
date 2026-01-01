"""
Security module for encryption and authentication
"""
from cryptography.fernet import Fernet
import bcrypt
import secrets

class SecurityManager:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data like bank tokens"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data).decode()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt)
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed)
    
    def generate_api_key(self):
        """Generate secure API key"""
        return secrets.token_urlsafe(32)