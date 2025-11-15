import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import sqlite3


def encrypt_and_store_entry(dateantime: str, entry: str, env):
    key = env["FERNET_KEY"]
    fernet = Fernet(key.encode())
    encrypted_date = fernet.encrypt(dateantime.encode())
    encrypted_entry = fernet.encrypt(entry.encode())

    conn = sqlite3.connect("diary.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO entrys (dateandtime, entry) VALUES (?, ?)", (encrypted_date, encrypted_entry))
    conn.commit()
    conn.close()


def decrypt_entry(env):
    key = env["FERNET_KEY"]
    fernet = Fernet(key.encode())
    conn = sqlite3.connect("diary.db")
    cursor = conn.cursor()
    dick = [{"id": ide ,"dateandtime": fernet.decrypt(date).decode(), "entry": fernet.decrypt(entry).decode()} for ide, date, entry in cursor.execute("SELECT id, dateandtime, entry FROM entrys")] 
    conn.close()
    return dick