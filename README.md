# 🔐 SecureCompress

**Ma'lumotlarni siqish va shifrlash orqali axborot sirqishini oldini oluvchi web tizim**

---

## 📁 Loyiha tuzilmasi

```
SecureCompress/
├── app.py                  # Flask asosiy fayl (REST API + sahifalar)
├── crypto_utils.py         # AES-256-GCM shifrlash/shifr ochish
├── compression_utils.py    # gzip/zip siqish
├── scanner.py              # Maxfiy ma'lumotlarni aniqlash (regex)
├── requirements.txt        # Python kutubxonalar
├── instance/
│   └── securecompress.db   # SQLite database (avtomatik yaratiladi)
├── static/
│   ├── css/
│   │   └── style.css       # Dark theme, glassmorphism UI
│   ├── js/
│   │   ├── script.js       # Global funksiyalar (toast, animatsiya)
│   │   └── upload.js       # Upload sahifasi logikasi
│   └── uploads/            # Shifrlangan fayllar saqlash joyi
└── templates/
    ├── base.html           # Asosiy shablon (navbar, footer)
    ├── index.html          # Bosh sahifa
    ├── upload.html         # Fayl yuklash sahifasi
    ├── verify.html         # Hash tekshiruvi sahifasi
    ├── history.html        # Fayl tarixi
    ├── security.html       # Xavfsizlik bo'yicha qo'llanma
    └── admin.html          # Admin panel
```

---

## ⚙️ O'rnatish va ishga tushirish

### 1. Virtual muhit yaratish (tavsiya etiladi)
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Ishga tushirish
```bash
python app.py
```

### 4. Brauzerda ochish
```
http://localhost:5000
```

---

## 🔑 Admin hisobi
- **Email:** admin@securecompress.uz
- **Parol:** Admin@12345

---

## 🛡️ Xavfsizlik xususiyatlari

| Xususiyat | Texnologiya |
|-----------|-------------|
| Shifrlash | AES-256-GCM |
| Kalit hosil qilish | PBKDF2-HMAC-SHA256 (200,000 iteratsiya) |
| Hash tekshiruvi | SHA-256 |
| Siqish | gzip Level-9 |
| Maxfiy ma'lumot skaneri | Regex (email, telefon, kredit karta, API key, JWT, SSH) |
| Fayl avtomatik o'chirish | 24 soat |

---

## 📡 API Endpointlar

| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/api/upload` | Fayl yuklash, siqish, shifrlash |
| POST | `/api/download/<id>` | Fayl yuklab olish (parol bilan) |
| POST | `/api/verify` | Hash tekshiruvi |
| GET | `/api/file/<id>` | Fayl ma'lumotlari |
| GET | `/api/stats` | Statistika |

---

## 🎨 UI xususiyatlari
- Dark theme (`#060D1A`)
- Gold accent (`#F5C842`)
- Glassmorphism kartalar
- Animatsion progress qadam ko'rsatgich
- Parol kuchi ko'rsatgich
- Responsive dizayn
- Toast bildirishnomalar
# SecureCompress
