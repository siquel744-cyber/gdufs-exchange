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

def hash_password(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()

def ensure_db():
    conn = sqlite3.connect(DB)
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
    cur.close()
    conn.close()

def main():
    ensure_db()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for username in ADMINS:
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        if row:
            user_id = row[0]
            print(f'用户已存在：{username} (id={user_id}), 设置为管理员')
            cur.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user_id,))
        else:
            random_pw = uuid.uuid4().hex
            pw_hash = hash_password(random_pw)
            created_at = datetime.utcnow().isoformat()
            cur.execute('INSERT INTO users (username, password_hash, created_at, is_admin, is_banned) VALUES (?, ?, ?, 1, 0)', (username, pw_hash, created_at))
            user_id = cur.lastrowid
            print(f'已创建用户：{username} (id={user_id}), 临时密码已随机生成。')
    conn.commit()
    cur.close()
    conn.close()
    print('管理员设置完成。')

if __name__ == '__main__':
    main()
