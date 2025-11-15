import sqlite3
import os


conn = sqlite3.connect('diary.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS entrys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dateandtime BLOB NOT NULL,
    entry BLOB NOT NULL
)
""")



conn.commit()
conn.close()