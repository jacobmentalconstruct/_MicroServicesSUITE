import hashlib
import time
import json
import base64
from typing import Optional, Dict

class AuthMS:
    """
    The Gatekeeper: Manages user authentication and session tokens.
    """
    def __init__(self, secret_key: str = "super_secret_cortex_key"):
        self.secret_key = secret_key
        # In a real scenario, this might load from a secure config file or DB
        self.users_db = {
            "admin": self._hash_password("admin123")
        }

    def login(self, username, password) -> Optional[str]:
        """
        Attempts to log in. Returns a session token if successful, None otherwise.
        """
        if username not in self.users_db:
            return None
        
        stored_hash = self.users_db[username]
        if self._verify_password(password, stored_hash):
            return self._create_token(username)
        
        return None

    def validate_session(self, token: str) -> bool:
        """
        Checks if a token is valid and not expired.
        """
        payload = self._decode_token(token)
        if payload:
            return True
        return False

    def _hash_password(self, password: str) -> str:
        """
        Securely hashes a password using SHA-256 (Simulated salt).
        """
        salt = "cortex_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a provided password against the stored hash.
        """
        return self._hash_password(plain_password) == hashed_password

    def _create_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Generates a signed session token.
        Payload includes 'sub' (subject) and 'exp' (expiration).
        """
        payload = {
            "sub": user_id,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
            "scope": "admin"
        }
        
        # Create the token parts
        json_payload = json.dumps(payload).encode()
        token_part = base64.b64encode(json_payload).decode()
        
        # Sign it
        signature = hashlib.sha256((token_part + self.secret_key).encode()).hexdigest()
        
        return f"{token_part}.{signature}"

    def _decode_token(self, token: str) -> Optional[Dict]:
        """
        Parses and validates the incoming token.
        Returns the payload if valid, None otherwise.
        """
        try:
            if not token or "." not in token:
                return None

            token_part, signature = token.split('.')
            
            # Re-calculate signature to verify integrity
            recalc_signature = hashlib.sha256((token_part + self.secret_key).encode()).hexdigest()
            
            if signature != recalc_signature:
                return None # Invalid Signature
            
            # Decode payload
            payload_json = base64.b64decode(token_part).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            if payload['exp'] < time.time():
                return None # Expired
                
            return payload
        except Exception:
            return None

# --- Independent Test Block ---
if __name__ == "__main__":
    print("--- Auth Service Test ---")
    auth = AuthMS()
    
    # 1. Test Login Success
    print("Attempting login (admin / admin123)...")
    token = auth.login("admin", "admin123")
    
    if token:
        print(f"Login Success! Token: {token[:20]}...")
        
        # 2. Test Validation
        is_valid = auth.validate_session(token)
        print(f"Token Valid? {is_valid}")
    else:
        print("Login Failed.")

    # 3. Test Login Fail
    print("\nAttempting login (admin / wrongpass)...")
    bad_token = auth.login("admin", "wrongpass")
    if not bad_token:
        print("Login Failed (Expected).")