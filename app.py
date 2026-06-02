import os
import sqlite3
import hashlib
import uuid
from datetime import datetime
from flask import Flask, g, request, jsonify, session, render_template, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "campus_market.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__, static_folder='static', template_folder='.', static_url_path='/static')
app.secret_key = os.environ.get("SECRET_KEY", "campus-market-secret-key")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        g._database = db
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            is_banned INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            seller TEXT NOT NULL,
            contact TEXT NOT NULL,
            category TEXT NOT NULL,
            image_url TEXT NOT NULL,
            description TEXT NOT NULL,
            sold INTEGER NOT NULL DEFAULT 0,
            owner_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
        """
    )
    # If upgrading an existing DB, ensure columns exist
    cur = db.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    cur.close()
    if 'is_admin' not in cols:
        db.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0')
    if 'is_banned' not in cols:
        db.execute('ALTER TABLE users ADD COLUMN is_banned INTEGER NOT NULL DEFAULT 0')
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/my-products')
def my_products_page():
    return render_template('my_products.html')


@app.route('/uploads/<path:filename>')
def upload_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route('/api/session', methods=['GET'])
def get_session():
    if 'user_id' in session:
        user = query_db('SELECT id, username, is_admin, is_banned FROM users WHERE id = ?', (session['user_id'],), one=True)
        if user:
            return jsonify({
                'logged_in': True,
                'username': session.get('username'),
                'user_id': session.get('user_id'),
                'is_admin': bool(user['is_admin']),
                'is_banned': bool(user['is_banned'])
            })
    return jsonify({
        'logged_in': False,
        'username': None,
        'user_id': None,
        'is_admin': False,
        'is_banned': False
    })


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空。'}), 400

    existing = query_db('SELECT id FROM users WHERE username = ?', (username,), one=True)
    if existing:
        return jsonify({'error': '用户名已存在，请直接登录。'}), 400

    execute_db(
        'INSERT INTO users (username, password_hash, created_at, is_admin, is_banned) VALUES (?, ?, ?, 0, 0)',
        (username, hash_password(password), datetime.utcnow().isoformat())
    )

    return jsonify({'success': True, 'message': '注册成功，请登录。'})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空。'}), 400

    user = query_db('SELECT id, password_hash, is_banned FROM users WHERE username = ?', (username,), one=True)
    if not user or hash_password(password) != user['password_hash']:
        return jsonify({'error': '用户名或密码错误。'}), 401
    if user['is_banned']:
        return jsonify({'error': '您的账号已被封禁，请联系管理员。'}), 403

    session['user_id'] = user['id']
    session['username'] = username
    return jsonify({'success': True, 'username': username, 'user_id': user['id']})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/products', methods=['GET', 'POST'])
def products():
    if request.method == 'GET':
        search = (request.args.get('q') or '').strip().lower()
        query = "SELECT p.*, u.username AS owner FROM products p LEFT JOIN users u ON p.owner_id = u.id"
        params = []
        if search:
            query += " WHERE LOWER(p.title) LIKE ? OR LOWER(p.category) LIKE ? OR LOWER(p.seller) LIKE ? OR LOWER(p.description) LIKE ?"
            keyword = f'%{search}%'
            params = [keyword, keyword, keyword, keyword]
        query += " ORDER BY p.created_at DESC"
        rows = query_db(query, params)
        return jsonify([dict(row) for row in rows])

    if 'user_id' not in session:
        return jsonify({'error': '登录后才能发布商品。'}), 403
    # check banned
    user = query_db('SELECT is_banned FROM users WHERE id = ?', (session['user_id'],), one=True)
    if user and user['is_banned']:
        return jsonify({'error': '您的账号已被封禁，无法发布商品。'}), 403

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    price = data.get('price')
    contact = (data.get('contact') or '').strip()
    category = (data.get('category') or '').strip() or '其他'
    image_url = (data.get('image_url') or '').strip()
    description = (data.get('description') or '').strip() or '暂无补充描述。'

    if not title or not price or not contact or not image_url:
        return jsonify({'error': '请补全商品名称、价格、联系方式和图片链接。'}), 400

    owner_id = session['user_id']
    seller = session.get('username', '校园卖家')
    created_at = datetime.utcnow().isoformat()

    product_id = execute_db(
        'INSERT INTO products (title, price, seller, contact, category, image_url, description, sold, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)',
        (title, int(price), seller, contact, category, image_url, description, owner_id, created_at)
    )

    product = query_db('SELECT p.*, u.username AS owner FROM products p LEFT JOIN users u ON p.owner_id = u.id WHERE p.id = ?', (product_id,), one=True)
    return jsonify(dict(product))


@app.route('/api/my-products', methods=['GET'])
def my_products():
    if 'user_id' not in session:
        return jsonify({'error': '请先登录。'}), 403
    rows = query_db(
        'SELECT p.*, u.username AS owner FROM products p LEFT JOIN users u ON p.owner_id = u.id WHERE p.owner_id = ? ORDER BY p.created_at DESC',
        (session['user_id'],)
    )
    return jsonify([dict(row) for row in rows])


@app.route('/api/products/<int:product_id>/sold', methods=['POST'])
def mark_sold(product_id):
    if 'user_id' not in session:
        return jsonify({'error': '登录后才能标记售出。'}), 403

    product = query_db('SELECT owner_id, sold FROM products WHERE id = ?', (product_id,), one=True)
    if not product:
        return jsonify({'error': '商品不存在。'}), 404
    if product['owner_id'] != session['user_id']:
        return jsonify({'error': '只有商品发布者可以标记售出。'}), 403
    if product['sold']:
        return jsonify({'error': '该商品已标记为售出。'}), 400

    execute_db('UPDATE products SET sold = 1 WHERE id = ?', (product_id,))
    return jsonify({'success': True})


@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return jsonify({'error': '登录后才能上传图片。'}), 403

    if 'image' not in request.files:
        return jsonify({'error': '未找到上传文件。'}), 400

    file = request.files['image']
    filename = secure_filename(file.filename)
    if not filename or '.' not in filename:
        return jsonify({'error': '文件名无效。'}), 400

    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({'error': '仅支持 PNG、JPG、JPEG、GIF 格式。'}), 400

    saved_name = f"{uuid.uuid4().hex}.{extension}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)
    file.save(saved_path)
    image_url = f"/uploads/{saved_name}"
    return jsonify({'success': True, 'image_url': image_url})


def require_admin():
    if 'user_id' not in session:
        return False
    user = query_db('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],), one=True)
    return bool(user and user['is_admin'])


@app.route('/admin')
def admin_page():
    if not require_admin():
        return render_template('index.html')
    return render_template('admin.html')


@app.route('/api/admin/users', methods=['GET'])
def admin_list_users():
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    rows = query_db('SELECT id, username, is_admin, is_banned, created_at FROM users ORDER BY created_at DESC')
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/users/<int:user_id>/set_admin', methods=['POST'])
def admin_set_admin(user_id):
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    data = request.get_json() or {}
    val = 1 if data.get('is_admin') else 0
    execute_db('UPDATE users SET is_admin = ? WHERE id = ?', (val, user_id))
    return jsonify({'success': True})


@app.route('/api/admin/users/<int:user_id>/set_ban', methods=['POST'])
def admin_set_ban(user_id):
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    data = request.get_json() or {}
    val = 1 if data.get('is_banned') else 0
    execute_db('UPDATE users SET is_banned = ? WHERE id = ?', (val, user_id))
    return jsonify({'success': True})


@app.route('/api/admin/products', methods=['GET'])
def admin_list_products():
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    rows = query_db('SELECT p.id, p.title, p.price, p.seller, p.sold, p.created_at, p.owner_id FROM products p ORDER BY p.created_at DESC')
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/products/<int:product_id>/force_sold', methods=['POST'])
def admin_force_sold(product_id):
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    execute_db('UPDATE products SET sold = 1 WHERE id = ?', (product_id,))
    return jsonify({'success': True})


@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
def admin_delete_product(product_id):
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    execute_db('DELETE FROM products WHERE id = ?', (product_id,))
    return jsonify({'success': True})


@app.route('/api/admin/reports', methods=['GET'])
def admin_list_reports():
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    # If reports table doesn't exist, return empty
    cur = get_db().execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
    exists = cur.fetchone()
    cur.close()
    if not exists:
        return jsonify([])
    rows = query_db('SELECT * FROM reports ORDER BY created_at DESC')
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/reports/<int:report_id>/resolve', methods=['POST'])
def admin_resolve_report(report_id):
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    execute_db('UPDATE reports SET handled = 1 WHERE id = ?', (report_id,))
    return jsonify({'success': True})


@app.route('/api/admin/reports/<int:report_id>', methods=['DELETE'])
def admin_delete_report(report_id):
    if not require_admin():
        return jsonify({'error': '权限不足'}), 403
    execute_db('DELETE FROM reports WHERE id = ?', (report_id,))
    return jsonify({'success': True})


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
