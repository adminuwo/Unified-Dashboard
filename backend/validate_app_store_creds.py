import os
from dotenv import load_dotenv

def validate_env():
    load_dotenv()
    
    required_keys = [
        "APP_STORE_CONNECT_ISSUER_ID",
        "APP_STORE_CONNECT_RUNTIME_KEY_ID",
        "APP_STORE_CONNECT_RUNTIME_PRIVATE_KEY_PATH",
        "APP_STORE_CONNECT_BOOTSTRAP_KEY_ID",
        "APP_STORE_CONNECT_BOOTSTRAP_PRIVATE_KEY_PATH",
        "AISA_APP_STORE_CONNECT_APP_ID",
        "AISA_APPLE_APP_ID",
        "AISA_BUNDLE_ID",
        "AI_LEGAL_APP_STORE_CONNECT_APP_ID",
        "AI_LEGAL_APPLE_APP_ID",
        "AI_LEGAL_BUNDLE_ID"
    ]
    
    missing = []
    for key in required_keys:
        if not os.getenv(key):
            missing.append(key)
            
    if missing:
        print("❌ Missing the following App Store credentials in your .env file:")
        for m in missing:
            print(f"   - {m}")
        print("\nPlease add them to your .env file before we proceed with the integration.")
    else:
        print("✅ All App Store credentials validated successfully!")

if __name__ == "__main__":
    validate_env()
