"""
SecureCompress - Ma'lumotlarni siqish va shifrlash tizimi
Production-grade Flask application
"""

import os
import re
import io
import gzip
import uuid
import hashlib
import logging
import zipfile
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, request, jsonify, render_template,
    send_file, abort, session, redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from crypto_utils import encrypt_data, decrypt_data, derive_key
from compression_utils import compress_file, get_compression_ratio
from scanner import scan_sensitive_data

# ─── App Config ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv',
    'json', 'xml', 'log', 'md', 'py', 'js', 'html', 'css',
    'jpg', 'jpeg', 'png', 'gif', 'zip', 'tar'
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'securecompress.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

db = SQLAlchemy(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Models ──────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship('FileRecord', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FileRecord(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(256), nullable=False)
    original_size = db.Column(db.Integer, nullable=False)
    compressed_size = db.Column(db.Integer, nullable=False)
    hash_sha256 = db.Column(db.String(64), nullable=False)
    warnings = db.Column(db.Text, default='[]')
    stored_path = db.Column(db.String(512), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at


class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    details = db.Column(db.Text, default='')
    ip_address = db.Column(db.String(64), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024**2):.1f} MB"
    return f"{size_bytes / (1024**3):.1f} GB"


def log_action(action, status, details=''):
    try:
        entry = Log(
            action=action,
            status=status,
            details=details,
            ip_address=request.remote_addr or ''
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"Log error: {e}")


def cleanup_expired_files():
    expired = FileRecord.query.filter(FileRecord.expires_at < datetime.utcnow()).all()
    for record in expired:
        try:
            if os.path.exists(record.stored_path):
                os.remove(record.stored_path)
            db.session.delete(record)
        except Exception as e:
            logger.error(f"Cleanup error for {record.file_id}: {e}")
    db.session.commit()


# ─── Routes: Pages ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/result')
def result_page():
    return render_template('result.html')

@app.route('/verify')
def verify_page():
    return render_template('verify.html')

@app.route('/security')
def security_page():
    return render_template('security.html')

@app.route('/history')
def history_page():
    cleanup_expired_files()
    records = FileRecord.query.order_by(FileRecord.created_at.desc()).limit(50).all()
    return render_template('history.html', records=records)

@app.route('/admin')
def admin_page():
    stats = {
        'total_files': FileRecord.query.count(),
        'total_users': User.query.count(),
        'total_logs': Log.query.count(),
        'recent_logs': Log.query.order_by(Log.created_at.desc()).limit(20).all(),
        'recent_files': FileRecord.query.order_by(FileRecord.created_at.desc()).limit(10).all(),
    }
    return render_template('admin.html', stats=stats)


# ─── API: Upload & Process ────────────────────────────────────────────────────

@app.route('/api/upload', methods=['POST'])
def api_upload():
    cleanup_expired_files()

    # Validation
    if 'file' not in request.files:
        return jsonify({'error': 'Fayl topilmadi'}), 400

    file = request.files['file']
    password = request.form.get('password', '').strip()

    if not file or file.filename == '':
        return jsonify({'error': 'Fayl tanlanmagan'}), 400

    if not allowed_file(file.filename):
        log_action('UPLOAD', 'REJECTED', f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Fayl turi ruxsat etilmagan'}), 400

    if not password:
        return jsonify({'error': 'Parol kiritilishi shart'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Parol kamida 6 belgi bo\'lishi kerak'}), 400

    try:
        filename = secure_filename(file.filename)
        file_data = file.read()
        original_size = len(file_data)

        if original_size == 0:
            return jsonify({'error': 'Fayl bo\'sh'}), 400

        # 1. Sensitive data scan (original content)
        text_content = ''
        try:
            text_content = file_data.decode('utf-8', errors='ignore')
        except Exception:
            pass
        warnings = scan_sensitive_data(text_content)

        # 2. Compute original hash
        original_hash = hashlib.sha256(file_data).hexdigest()

        # 3. Compress
        compressed_data = compress_file(file_data, filename)
        compressed_size = len(compressed_data)

        # 4. Encrypt
        encrypted_data = encrypt_data(compressed_data, password)

        # 5. Save to disk
        file_id = str(uuid.uuid4())
        stored_filename = f"{file_id}.sec"
        stored_path = os.path.join(UPLOAD_FOLDER, stored_filename)

        with open(stored_path, 'wb') as f:
            f.write(encrypted_data)

        # 6. DB record
        import json
        record = FileRecord(
            file_id=file_id,
            filename=filename,
            original_size=original_size,
            compressed_size=compressed_size,
            hash_sha256=original_hash,
            warnings=json.dumps(warnings),
            stored_path=stored_path,
        )
        db.session.add(record)
        db.session.commit()

        ratio = get_compression_ratio(original_size, compressed_size)

        log_action('UPLOAD', 'SUCCESS', f"File: {filename}, ID: {file_id}")

        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'original_size': format_size(original_size),
            'compressed_size': format_size(compressed_size),
            'encrypted_size': format_size(len(encrypted_data)),
            'compression_ratio': f"{ratio:.1f}%",
            'hash': original_hash,
            'warnings': warnings,
            'expires_in': '24 soat'
        })

    except Exception as e:
        logger.exception("Upload error")
        log_action('UPLOAD', 'ERROR', str(e))
        return jsonify({'error': 'Server xatosi yuz berdi'}), 500


# ─── API: Download ────────────────────────────────────────────────────────────

@app.route('/api/download/<file_id>', methods=['POST'])
def api_download(file_id):
    record = FileRecord.query.filter_by(file_id=file_id).first()
    if not record:
        return jsonify({'error': 'Fayl topilmadi'}), 404

    if record.is_expired:
        return jsonify({'error': 'Fayl muddati tugagan'}), 410

    password = request.form.get('password', '').strip()
    if not password:
        return jsonify({'error': 'Parol kiritilishi shart'}), 400

    try:
        with open(record.stored_path, 'rb') as f:
            encrypted_data = f.read()

        decrypted_compressed = decrypt_data(encrypted_data, password)
        if decrypted_compressed is None:
            log_action('DOWNLOAD', 'FAILED', f"Wrong password for {file_id}")
            return jsonify({'error': 'Noto\'g\'ri parol'}), 403

        # Decompress
        try:
            with gzip.open(io.BytesIO(decrypted_compressed), 'rb') as gz:
                original_data = gz.read()
        except Exception:
            original_data = decrypted_compressed

        log_action('DOWNLOAD', 'SUCCESS', f"File ID: {file_id}")

        return send_file(
            io.BytesIO(original_data),
            as_attachment=True,
            download_name=record.filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.exception("Download error")
        log_action('DOWNLOAD', 'ERROR', str(e))
        return jsonify({'error': 'Yuklab olishda xato yuz berdi'}), 500


# ─── API: Verify Hash ─────────────────────────────────────────────────────────

@app.route('/api/verify', methods=['POST'])
def api_verify():
    if 'file' not in request.files:
        return jsonify({'error': 'Fayl topilmadi'}), 400

    file = request.files['file']
    original_hash = request.form.get('hash', '').strip().lower()

    if not original_hash or len(original_hash) != 64:
        return jsonify({'error': 'Noto\'g\'ri hash format (SHA-256 kerak)'}), 400

    try:
        file_data = file.read()
        computed_hash = hashlib.sha256(file_data).hexdigest()
        is_valid = computed_hash == original_hash

        log_action('VERIFY', 'VALID' if is_valid else 'TAMPERED', f"Hash match: {is_valid}")

        return jsonify({
            'status': 'valid' if is_valid else 'tampered',
            'computed_hash': computed_hash,
            'provided_hash': original_hash,
            'match': is_valid
        })

    except Exception as e:
        logger.exception("Verify error")
        return jsonify({'error': 'Tekshirishda xato'}), 500


# ─── API: File Info ───────────────────────────────────────────────────────────

@app.route('/api/file/<file_id>', methods=['GET'])
def api_file_info(file_id):
    record = FileRecord.query.filter_by(file_id=file_id).first()
    if not record:
        return jsonify({'error': 'Topilmadi'}), 404

    import json
    return jsonify({
        'file_id': record.file_id,
        'filename': record.filename,
        'original_size': format_size(record.original_size),
        'compressed_size': format_size(record.compressed_size),
        'hash': record.hash_sha256,
        'warnings': json.loads(record.warnings or '[]'),
        'created_at': record.created_at.isoformat(),
        'expires_at': record.expires_at.isoformat(),
        'expired': record.is_expired
    })


# ─── API: Stats ───────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def api_stats():
    return jsonify({
        'total_files': FileRecord.query.count(),
        'total_logs': Log.query.count(),
        'total_size_saved': db.session.query(
            db.func.sum(FileRecord.original_size - FileRecord.compressed_size)
        ).scalar() or 0
    })


# ─── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Fayl hajmi juda katta (max 50MB)'}), 413

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server xatosi'}), 500


# ─── Init DB ──────────────────────────────────────────────────────────────────

def init_db():
    with app.app_context():
        db.create_all()
        # Create demo admin user if not exists
        if not User.query.filter_by(email='admin@securecompress.uz').first():
            admin = User(email='admin@securecompress.uz', is_admin=True)
            admin.set_password('Admin@12345')
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created: admin@securecompress.uz / Admin@12345")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
