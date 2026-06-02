import sqlite3
import os
import hashlib
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, 'campus_market.db')
ADMINS = [
    '20240401317',
    '20240401459'
]
NEW_PASSWORD = 'gdufs2026'

def hash_password(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()

def ensure_tables(conn):
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        is_banned INTEGER NOT NULL DEFAULT 0
    )''')
    conn.commit()

def main():
    conn = sqlite3.connect(DB)
    ensure_tables(conn)
    cur = conn.cursor()
    pw_hash = hash_password(NEW_PASSWORD)
    for username in ADMINS:
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        if row:
            uid = row[0]
            cur.execute('UPDATE users SET password_hash = ?, is_admin = 1 WHERE id = ?', (pw_hash, uid))
            print(f'更新用户 {username} 密码并设为管理员 (id={uid})')
        else:
            created_at = datetime.utcnow().isoformat()
            cur.execute('INSERT INTO users (username, password_hash, created_at, is_admin, is_banned) VALUES (?, ?, ?, 1, 0)', (username, pw_hash, created_at))
            uid = cur.lastrowid
            print(f'创建用户 {username} 并设置密码、管理员 (id={uid})')
    conn.commit()
    cur.close()
    conn.close()
    print('完成：已为指定学号设置密码为 gdufs2026。')

if __name__ == '__main__':
    main()
