import time
import hmac
import hashlib
import requests

API_KEY = "3E19KfDSumU6bE7ATuHojy6tNJRSVGJhHDsn8puzk1joKyCBBpyC34d8zMmPWevDup"
API_SECRET = "Ohasz9vZhaxegr4WlIggKdpS6pKvMJI8h4NzR4XbeyhWN5uvzRmnbdIO0MBYQE5Q"
BASE_URL = "http://127.0.0.1:8000"

timestamp = str(int(time.time() * 1000))
params = {
    "symbol": "BTC_USDT",
    "limit": "1",
    "timestamp": timestamp
}

# Step 3: Sort params and build query string
sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
path = "/api/v1/test/signature"
path_url = f"{path}?{sorted_params}"

# Step 5: method + path_url
to_sign = f"GET{path_url}"

# Step 7: HMAC SHA256 signature
signature = hmac.new(
    API_SECRET.encode(),
    to_sign.encode(),
    hashlib.sha256
).hexdigest()

# Step 8: Send request
headers = {
    "PIONEX-SIGNATURE": signature
}

res = requests.get(f"{BASE_URL}{path_url}", headers=headers)
print(res.status_code)
print(res.json())
