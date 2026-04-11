from cryptography.fernet import Fernet
import psycopg2

def encrypt_and_store_entry(dateantime: str, entry: str, img: str | None, env):
    key = env["FERNET_KEY"]
    fernet = Fernet(key.encode())
    encrypted_date = fernet.encrypt(dateantime.encode())
    encrypted_entry = fernet.encrypt(entry.encode())
    if img is not None:
            encrypted_image = fernet.encrypt(img.encode())
    else:
        encrypted_image = None
    conn = psycopg2.connect(env['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entrys (dateandtime, entry, img) VALUES (%s, %s, %s)", (encrypted_date, encrypted_entry, encrypted_image))
    conn.commit()
    cursor.close()
    conn.close()


def decrypt_entry(env):
    key = env["FERNET_KEY"]
    fernet = Fernet(key.encode())
    conn = psycopg2.connect(env['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute("SELECT id, dateandtime, entry, img FROM entrys ORDER BY id ASC;")
    rows = cursor.fetchall()
    dick = []
    for ide, date, entry, img in rows:
        decrypted_image = fernet.decrypt(bytes(img)).decode() if img is not None else None
        
        dick.append({
            "id": ide,
            "dateandtime": fernet.decrypt(bytes(date)).decode(),
            "entry": fernet.decrypt(bytes(entry)).decode(),
            "image": decrypted_image
        })
        
    conn.close()
    
    return dick


def delete_entry(entry_id, env):
    conn = psycopg2.connect(env['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute('DELETE FROM entrys WHERE id=%s', (entry_id,))
    conn.commit()
    conn.close()


# создание ключа в формате байтов 
# key = Fernet.generate_key()

