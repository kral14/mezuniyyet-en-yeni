# Məzuniyyət Sistemi v6.7 - Səliqəli Struktur

## 📋 Təsvir

Məzuniyyət Sistemi - çoxlu şirkət dəstəyi olan, universal link sistemi ilə işləyən, tam funksional məzuniyyət idarəetmə tətbiqidir. **Yeni səliqəli struktur ilə təşkil edilib.**

## 🏗️ Yeni Fayl Strukturu

```
mezuniyyet-sistemi/
├── src/                          # Əsas mənbə kodları
│   ├── core/                     # Əsas funksiyalar
│   │   ├── main.py              # Əsas tətbiq
│   │   └── tenant_manager.py    # Şirkət idarəetməsi
│   ├── ui/                      # İstifadəçi interfeysi
│   │   ├── auth.py              # Giriş/qeydiyyat
│   │   ├── components.py        # UI komponentləri
│   │   ├── vacation_tree.py     # Məzuniyyət ağacı
│   │   └── ...                  # Digər UI faylları
│   ├── database/                # Veritaban modulları
│   │   ├── database.py          # Əsas veritaban
│   │   ├── sqlite_db.py         # SQLite dəstəyi
│   │   ├── manager.py           # Veritaban meneceri
│   │   └── ...                  # Digər DB faylları
│   ├── api/                     # API server
│   │   ├── server.py            # FastAPI server
│   │   └── client.py            # API client
│   ├── utils/                   # Köməkçi funksiyalar
│   │   ├── cache.py             # Cache idarəetməsi
│   │   ├── updater.py           # Yeniləmə sistemi
│   │   └── ...                  # Digər utility faylları
│   ├── config/                  # Konfiqurasiya
│   │   ├── version.txt          # Versiya məlumatı
│   │   ├── version.txt          # Versiya məlumatı
│   │   └── requirements.txt     # Tələb olunan kitabxanalar
│   ├── tests/                   # Test faylları
│   ├── build/                   # Build faylları
│   ├── docs/                    # Sənədlər
│   └── assets/                  # Resurslar
│       └── icons/               # İkonlar
├── main.py                      # Əsas başlatma faylı
└── README.md                    # Bu fayl
```

## ✨ Əsas Xüsusiyyətlər

### 🔗 Universal Link Sistemi
- Hər şirkət üçün unikal link yaradılır
- Link ilə asan qoşulma
- Unudulmuş linkləri tapmaq üçün axtarış sistemi

### 🏢 Çoxlu Şirkət Dəstəyi
- Hər şirkət öz veritabanı ilə işləyir
- Mərkəzi server ilə idarəetmə
- Şirkət məlumatlarının təhlükəsiz saxlanması

### 👥 İstifadəçi İdarəetməsi
- Admin və adi istifadəçi rolları
- Çoxlu sessiya dəstəyi
- Giriş tarixçəsi

### 📅 Məzuniyyət İdarəetməsi
- Məzuniyyət müraciətləri
- Təsdiq/redd sistemi
- Bildiriş sistemi
- Arxivləmə

### 🗄️ Çoxlu Veritaban Dəstəyi
- PostgreSQL
- MySQL
- SQLite
- SQL Server
- Oracle

## 🚀 Quraşdırma

### Tələb olunan sistemlər
- Python 3.8+
- Windows 10/11

### Kitabxanaların quraşdırılması
```bash
pip install -r src/config/requirements.txt
```

### Sistemin işə salınması
```bash
python main.py
```

## 🔧 Konfiqurasiya

### Yeni Şirkət Qeydiyyatı
1. Tətbiqi işə salın
2. "Admin (Yeni Şirkət Yaradacağam)" seçin
3. Şirkət adını və veritaban qoşulma sətrini daxil edin
4. Universal link avtomatik yaradılacaq

### Mövcud Şirkətə Qoşulma
1. Tətbiqi işə salın
2. "İstifadəçi (Mənə Verilən Linklə Qoşulacağam)" seçin
3. Universal linki daxil edin

### Unudulmuş Linki Tapmaq
1. Tətbiqi işə salın
2. "Admin (Unudulmuş Linki Tapacağam)" seçin
3. Connection string və ya şirkət adı ilə axtarın

## 🛠️ API Endpoint-ləri

### Mərkəzi Server
- `GET /health` - Server statusu
- `POST /api/tenants/create` - Yeni şirkət yaratmaq
- `GET /api/tenants/{tenant_id}` - Şirkət məlumatları
- `GET /api/tenants/search/{company_name}` - Şirkət axtarışı
- `GET /api/tenants/link/{connection_hash}` - Connection string ilə axtarış

## 🔒 Təhlükəsizlik

- Şifrələr bcrypt ilə hash edilir
- Sessiya idarəetməsi
- Connection string-lər təhlükəsiz saxlanılır
- HTTPS qoşulması

## 📊 Sistem Tələbləri

### Minimum
- RAM: 2GB
- Disk: 100MB
- İnternet qoşulması

### Tövsiyə olunan
- RAM: 4GB+
- Disk: 500MB+
- Sürətli internet qoşulması

## 🐛 Problemlərin həlli

### Veritabanı qoşulma xətası
1. Connection string-i yoxlayın
2. İnternet qoşulmasını yoxlayın
3. Veritaban serverinin işlək olduğunu yoxlayın

### Mərkəzi server xətası
1. İnternet qoşulmasını yoxlayın
2. Server statusunu yoxlayın: `https://mezuniyyet-serverim.onrender.com/health`

### Tətbiq açılmır
1. Python versiyasını yoxlayın (3.8+)
2. Kitabxanaları yenidən quraşdırın: `pip install -r src/config/requirements.txt`

## 📞 Dəstək

Problemlər üçün:
1. Log fayllarını yoxlayın
2. Test scriptini işə salın: `python src/tests/test_system.py`
3. Sistem tələblərini yoxlayın

## 📝 Versiya Tarixçəsi

### v6.7 (Cari) - Səliqəli Struktur
- Yeni fayl strukturu
- Modulyar təşkil
- Daha yaxşı kod təşkili
- Bütün xətalar düzəldilib

### v6.4
- Universal link sistemi
- Çoxlu veritaban dəstəyi
- Təkmilləşdirilmiş UI
- Mərkəzi server inteqrasiyası

### v6.3
- Tenant idarəetmə sistemi
- Relink funksiyası
- Təkmilləşdirilmiş təhlükəsizlik

### v6.2
- Çoxlu sessiya dəstəyi
- Giriş tarixçəsi
- Bildiriş sistemi

---

**Məzuniyyət Sistemi v6.7** - Professional məzuniyyət idarəetmə həlli (Səliqəli Struktur) 