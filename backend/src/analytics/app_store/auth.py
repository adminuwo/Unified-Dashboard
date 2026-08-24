import os
import time
try:
    import jwt  # PyJWT
except ImportError:
    from jose import jwt  # python-jose


class AppStoreConnectAuth:
    def __init__(self, issuer_id: str, key_id: str, private_key: str):
        self.issuer_id = issuer_id.strip() if issuer_id else ""
        self.key_id = key_id.strip() if key_id else ""
        pk = private_key.strip() if private_key else ""
        if os.path.exists(pk):
            with open(pk, "r", encoding="utf-8") as f:
                self.private_key = f.read().strip()
        else:
            self.private_key = pk
        
    def generate_token(self, expiration_minutes: int = 10) -> str:
        """
        Generate an ES256 signed JWT for the App Store Connect API.
        """
        now = int(time.time())
        exp = now + (expiration_minutes * 60)
        
        headers = {
            "alg": "ES256",
            "kid": self.key_id,
            "typ": "JWT"
        }
        
        payload = {
            "iss": self.issuer_id,
            "iat": now,
            "exp": exp,
            "aud": "appstoreconnect-v1"
        }
        
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="ES256",
            headers=headers
        )
        
        return token if isinstance(token, str) else token.decode("utf-8")

