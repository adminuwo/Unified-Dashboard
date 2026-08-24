import requests
from requests.auth import HTTPBasicAuth

# Base keys provided by user
base_key_id = "rzp_live_SPThiXBxRRJDla"
base_key_secret = "fj1Cq2ssyAkcbk7gQkb6yh8a"

# Character confusion dictionary
confusion = {
    '1': ['1', 'l', 'I', 'i'],
    'l': ['l', '1', 'I', 'i'],
    'i': ['i', '1', 'l', 'I'],
    'I': ['I', '1', 'l', 'i'],
}

def get_variations(s):
    # Find all indexes of confusing characters
    indexes = [idx for idx, char in enumerate(s) if char in confusion]
    if not indexes:
        return [s]
    
    variations = [s]
    # Simple brute force of combinations
    for idx in indexes:
        char = s[idx]
        current_vars = list(variations)
        for val in confusion[char]:
            for cv in current_vars:
                new_var = cv[:idx] + val + cv[idx+1:]
                if new_var not in variations:
                    variations.append(new_var)
    return variations

id_vars = get_variations(base_key_id)
secret_vars = get_variations(base_key_secret)

print(f"Generated {len(id_vars)} Key ID variations and {len(secret_vars)} Key Secret variations.")
print(f"Testing {len(id_vars) * len(secret_vars)} combinations...")

found = False
for kid in id_vars:
    for ksec in secret_vars:
        try:
            resp = requests.get(
                "https://api.razorpay.com/v1/payments",
                params={"count": 1},
                auth=HTTPBasicAuth(kid, ksec),
                timeout=5
            )
            if resp.status_code == 200:
                print(f"\nSUCCESS! Correct credentials found:")
                print(f"RAZORPAY_EFV_KEY_ID={kid}")
                print(f"RAZORPAY_EFV_KEY_SECRET={ksec}")
                found = True
                break
        except Exception:
            pass
    if found:
        break

if not found:
    print("\nNo combination succeeded. The credentials may have larger errors or be completely inactive.")
