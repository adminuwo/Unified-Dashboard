import time
import jwt

class AppStoreConnectAuth:
    def __init__(self, issuer_id: str, key_id: str, private_key: str):
        self.issuer_id = issuer_id
        self.key_id = key_id
        self.private_key = private_key
        
    def generate_token(self, expiration_minutes: int = 10) -> str:
        """
        Generate an ES256 signed JWT for the App Store Connect API.
        The token includes the issuer ID, issue time, expiration time, and audience.
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
        
        # Use pyjwt to encode and sign the token
        token = jwt.encode(
            payload=payload,
            key=self.private_key,
            algorithm="ES256",
            headers=headers
        )
        
        return token
