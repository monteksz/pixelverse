import imaplib
import email
from email.header import decode_header
from email import policy
from email.parser import BytesParser
import requests
import time
import re
from colorama import Fore, Style, init
from faker import Faker

# Inisialisasi colorama dan Faker
init(autoreset=True)
fake = Faker()

# Masukkan kredensial email untuk menerima OTP
imap_username = input("Masukan Email Hotmail/Outlook: ")
imap_password = input("Masukan Password: ")

# Fungsi untuk menghubungkan dan login ke IMAP
def connect_imap(username, password):
    mail = imaplib.IMAP4_SSL("imap-mail.outlook.com")
    mail.login(username, password)
    return mail

# Fungsi untuk mencari email dengan subjek tertentu
def search_email(mail, subject):
    mail.select("inbox")
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()
    
    for email_id in reversed(email_ids):
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = BytesParser(policy=policy.default).parsebytes(response_part[1])
                msg_subject = decode_header(msg["Subject"])[0][0]
                if isinstance(msg_subject, bytes):
                    msg_subject = msg_subject.decode()
                if subject in msg_subject:
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                return body
                    else:
                        body = msg.get_payload(decode=True).decode()
                        return body
    return None

# Fungsi untuk mengekstrak OTP dari body email
def extract_otp(body):
    otp_match = re.search(r'Here is your Pixelverse OTP: (\d+)', body)
    if otp_match:
        return otp_match.group(1)
    return None

# Fungsi untuk mengirim permintaan OTP
def request_otp(email):
    response = requests.post('https://api.pixelverse.xyz/api/otp/request', json={'email': email})
    return response.status_code == 200

# Fungsi untuk memverifikasi OTP
def verify_otp(email, otp):
    response = requests.post('https://api.pixelverse.xyz/api/auth/otp', json={'email': email, 'otpCode': otp})
    if response.status_code in [200, 201]:
        refresh_token_cookie = response.cookies.get('refresh-token')
        try:
            data = response.json()
        except ValueError:
            print(f"Respon JSON tidak valid untuk {email}. Status: {response.status_code}, Respon: {response.text}")
            return None

        data['refresh_token'] = refresh_token_cookie
        if 'tokens' in data and 'access' in data['tokens']:
            data['access_token'] = data['tokens']['access']
            return data
        else:
            print(f"Respon tidak mengandung tokens['access'] untuk {email}. Respon: {data}")
    else:
        print(f"Verifikasi OTP gagal. Status: {response.status_code}, Respon: {response.text}")
    return None

# Fungsi untuk mengatur referral
def set_referral(referral_code, access_token):
    headers = {
        'Authorization': access_token,  # tanpa 'Bearer'
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Origin': 'https://dashboard.pixelverse.xyz',
        'Referer': 'https://dashboard.pixelverse.xyz/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    referral_url = f'https://api.pixelverse.xyz/api/referrals/set-referer/{referral_code}'
    response = requests.put(referral_url, headers=headers)
    try:
        response_json = response.json()
    except ValueError:
        response_json = None
    return response.status_code, response_json

# Fungsi untuk memperbarui username dan biography
def update_username_and_bio(access_token):
    url = "https://api.pixelverse.xyz/api/users/@me"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Authorization': access_token,
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'https://dashboard.pixelverse.xyz',
        'Referer': 'https://dashboard.pixelverse.xyz/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    username = fake.user_name()
    biography = fake.sentence()
    payload = {
        "updateProfileOptions": {
            "username": username,
            "biography": biography
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(Fore.GREEN + Style.BRIGHT + f"Username berhasil diperbarui menjadi: {username}")
        print(Fore.GREEN + Style.BRIGHT + f"Bio berhasil diperbarui menjadi: {biography}")
    else:
        print(Fore.RED + Style.BRIGHT + f"Gagal memperbarui username. Status: {response.status_code}, Respon: {response.text}")
    return response.status_code == 200

# Fungsi untuk membeli pet
def buy_pet(access_token, pet_id):
    url = f"https://api.pixelverse.xyz/api/pets/{pet_id}/buy"
    headers = {
        'Authorization': access_token,
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Origin': 'https://dashboard.pixelverse.xyz',
        'Referer': 'https://dashboard.pixelverse.xyz/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    response = requests.post(url, headers=headers)
    if response.status_code in [200, 201]:
        print(Fore.GREEN + Style.BRIGHT + "Pet berhasil dibeli!")
        return response.status_code, response.json()
    else:
        print(Fore.RED + Style.BRIGHT + f"Gagal membeli pet. Status: {response.status_code}, Respon: {response.text}")
    return None, None

# Fungsi untuk memilih pet
def select_pet(access_token, pet_data):
    pet_id = pet_data['id']
    url = f"https://api.pixelverse.xyz/api/pets/user-pets/{pet_id}/select"
    headers = {
        'Authorization': access_token,
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Origin': 'https://dashboard.pixelverse.xyz',
        'Referer': 'https://dashboard.pixelverse.xyz/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        print(Fore.GREEN + Style.BRIGHT + "Pet berhasil dipilih!")
        return True
    elif response.status_code == 201:
        print(Fore.GREEN + Style.BRIGHT + "Pet sudah dipilih sebelumnya.")
        return True
    elif response.status_code == 400 and response.json().get('message') == "You have already selected this pet":
        print(Fore.GREEN + Style.BRIGHT + "Pet berhasil dipilih!")
        return True
    else:
        print(Fore.RED + Style.BRIGHT + f"Gagal memilih pet. Status: {response.status_code}, Respon: {response.text}")
    return False

# Fungsi untuk mengklaim daily reward
def claim_daily_reward(access_token):
    url = "https://api.pixelverse.xyz/api/daily-reward/complete"
    headers = {
        'Authorization': access_token,
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Origin': 'https://dashboard.pixelverse.xyz',
        'Referer': 'https://dashboard.pixelverse.xyz/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    try:
        response = requests.post(url, headers=headers)
        if response.status_code in [200, 201]:
            print(Fore.GREEN + Style.BRIGHT + "Daily reward berhasil diklaim!")
            return True
        else:
            print(Fore.RED + Style.BRIGHT + f"Gagal mengklaim daily reward. Status: {response.status_code}, Respon: {response.text}")
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"Gagal mengklaim daily reward: {str(e)}")
    return False

# Fungsi utama untuk mengatur jumlah referral yang diinginkan
def main():
    # Baca daftar email dari file data.txt
    with open('data.txt', 'r') as file:
        emails = [line.strip() for line in file.readlines()]

    # Kode referral
    referral_code = input("Masukan Code Refferal: ")

    # Input jumlah referral yang diinginkan
    desired_referrals = int(input("Masukkan jumlah referral yang diinginkan: "))

    # Hubungkan ke IMAP
    mail = connect_imap(imap_username, imap_password)

    # Proses setiap email
    successful_emails = []
    for index, email in enumerate(emails, start=1):
        if len(successful_emails) >= desired_referrals:
            break
        print(Fore.CYAN + Style.BRIGHT + f"Proses email Ke-{index}: {email}")
        if request_otp(email):
            print(Fore.YELLOW + Style.BRIGHT + f"OTP diminta untuk {email}. Tunggu beberapa detik...")
            time.sleep(10)  # Tunggu beberapa detik agar email OTP dapat diterima

            otp_subject = "Pixelverse Authorization"  # Sesuaikan dengan subjek email OTP yang diterima
            otp_body = search_email(mail, otp_subject)

            if otp_body:
                otp_code = extract_otp(otp_body)
                if otp_code:
                    print(Fore.GREEN + Style.BRIGHT + f"OTP diterima: {otp_code}")
                    auth_data = verify_otp(email, otp_code)

                    if auth_data and 'access_token' in auth_data:
                        access_token = auth_data['access_token']
                        print(Fore.GREEN + Style.BRIGHT + f"Token akses diterima")
                        status_code, response_json = set_referral(referral_code, access_token)
                        if status_code in [200, 201]:
                            print(Fore.GREEN + Style.BRIGHT + "Referral set berhasil.")
                            if update_username_and_bio(access_token):
                                pet_id = "27977f52-997c-45ce-9564-a2f585135ff5"
                                pet_status, pet_data = buy_pet(access_token, pet_id)
                                if pet_status in [200, 201]:
                                    if select_pet(access_token, pet_data):
                                        if claim_daily_reward(access_token):
                                            print(Fore.BLUE + Style.BRIGHT + f"Refferal Ke-{index} Berhasil")
                                            successful_emails.append(email)
                        else:
                            print(Fore.RED + Style.BRIGHT + f"Referral set gagal untuk {email}. Status: {status_code}, Respon: {response_json}")
                            print(Fore.RED + Style.BRIGHT + f"Refferal Ke-{index} Gagal")
                    else:
                        print(Fore.RED + Style.BRIGHT + f"Verifikasi OTP gagal untuk {email}. Tidak ada access_token dalam respon.")
                        print(Fore.RED + Style.BRIGHT + f"Refferal Ke-{index} Gagal")
                else:
                    print(Fore.RED + Style.BRIGHT + f"Tidak dapat mengekstrak OTP untuk {email}.")
                    print(Fore.RED + Style.BRIGHT + f"Refferal Ke-{index} Gagal")
            else:
                print(Fore.RED + Style.BRIGHT + f"Tidak dapat menemukan email OTP untuk {email}.")
                print(Fore.RED + Style.BRIGHT + f"Refferal Ke-{index} Gagal")
        else:
            print(Fore.RED + Style.BRIGHT + f"Permintaan OTP gagal untuk {email}.")
            print(Fore.RED + Style.BRIGHT + f"Refferal Ke-{index} Gagal")

    # Filter email yang gagal
    failed_emails = [email for email in emails if email not in successful_emails]

    # Tulis ulang email yang gagal ke file data.txt
    with open('data.txt', 'w') as file:
        for email in failed_emails:
            file.write(email + '\n')

    # Logout dari server IMAP
    mail.logout()

# Jalankan fungsi utama
if __name__ == "__main__":
    main()
