from cryptography.fernet import Fernet
import psycopg2

def encrypt_and_store_entry(dateantime: str, entry: str, env):
    key = env["FERNET_KEY"]
    fernet = Fernet(key.encode())
    encrypted_date = fernet.encrypt(dateantime.encode())
    encrypted_entry = fernet.encrypt(entry.encode())

    conn = psycopg2.connect(env['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entrys (dateandtime, entry) VALUES (%s, %s)", (encrypted_date, encrypted_entry))
    conn.commit()
    conn.close()


def decrypt_entry(env):
    key = env["FERNET_KEY"]
    fernet = Fernet(key.encode())
    conn = psycopg2.connect(env['DATABASE_URL'])
    cursor = conn.cursor()
    cursor.execute("SELECT id, dateandtime, entry FROM entrys")
    rows = cursor.fetchall()
    dick = [{"id": ide ,"dateandtime": fernet.decrypt(bytes(date)).decode(),
              "entry": fernet.decrypt(bytes(entry)).decode()}
                for ide, date, entry 
                in rows]
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

