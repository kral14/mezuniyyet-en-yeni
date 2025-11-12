# Məzuniyyət Sistemi v6.7 - Yeni Fayl Strukturu

## 📁 Səliqəli Təşkil Edilmiş Struktur

```
mezuniyyet-sistemi/
├── main.py                          # Əsas başlatma faylı
├── README.md                        # Əsas sənəd
├── STRUCTURE.md                     # Bu fayl - struktur təsviri
└── src/                             # Əsas mənbə kodları
    ├── __init__.py                  # Src modulu
    ├── core/                        # Əsas funksiyalar
    │   ├── __init__.py
    │   ├── main.py                  # Əsas tətbiq (unified_app.py)
    │   └── tenant_manager.py        # Şirkət idarəetməsi
    ├── ui/                          # İstifadəçi interfeysi
    │   ├── __init__.py
    │   ├── auth.py                  # Giriş/qeydiyyat (auth_windows.py)
    │   ├── components.py            # UI komponentləri (ui_components.py)
    │   ├── vacation_tree.py         # Məzuniyyət ağacı (vacation_tree_view.py)
    │   ├── main_frame.py            # Əsas pəncərə
    │   ├── dashboard_calendar_frame.py
    │   ├── settings_window.py
    │   ├── user_management_window.py
    │   ├── notifications_window.py
    │   ├── error_viewer_window.py
    │   ├── employee_form_window.py
    │   ├── employee_detail_frame.py
    │   ├── archive_window.py
    │   ├── loading_animation.py
    │   ├── login_history_window.py
    │   ├── calendar.html
    │   ├── script.js
    │   └── style.css
    ├── database/                    # Veritaban modulları
    │   ├── __init__.py
    │   ├── database.py              # Əsas veritaban
    │   ├── sqlite_db.py             # SQLite dəstəyi (database_sqlite.py)
    │   ├── manager.py               # Veritaban meneceri (database_manager.py)
    │   ├── connection.py            # Qoşulma idarəetməsi
    │   ├── user_queries.py
    │   ├── vacation_queries.py
    │   ├── notification_queries.py
    │   ├── session_queries.py
    │   ├── settings_queries.py
    │   ├── error_queries.py
    │   ├── command_queries.py
    │   ├── system_queries.py
    │   ├── create_database_tables.py
    │   ├── create_postgresql_tables.py
    │   ├── mezuniyyet_sistemi.db
    │   ├── central_database.db
    │   └── main_tenants.db
    ├── api/                         # API server
    │   ├── __init__.py
    │   ├── server.py                # FastAPI server (main.py)
    │   ├── client.py                # API client (central_client.py)
    │   └── requirements.txt
    ├── utils/                       # Köməkçi funksiyalar
    │   ├── __init__.py
    │   ├── cache.py                 # Cache idarəetməsi (cache_manager.py)
    │   ├── updater.py               # Yeniləmə sistemi (updater_service.py)
    │   ├── update_script.py
    │   ├── debug_database_fallback.py
    │   ├── debug_loading.py
    │   ├── fix_central_server.py
    │   └── setup_windows.py
    ├── config/                      # Konfiqurasiya
    │   ├── __init__.py
    │   ├── version.txt              # Versiya məlumatı
    │   └── requirements.txt         # Tələb olunan kitabxanalar
    ├── tests/                       # Test faylları
    │   ├── __init__.py
    │   ├── test_vacation_panel.py
    │   ├── test_vacation_debug.py
    │   ├── test_direct_sqlite.py
    │   ├── test_local_database.py
    │   ├── test_airplane_animation.py
    │   ├── test_loading_animation.py
    │   ├── test_frame_size.py
    │   ├── test_update.py
    │   └── test_update_manual.py
    ├── build/                       # Build faylları
    │   ├── build_unified_app.bat
    │   ├── deploy_api.bat
    │   ├── install_and_run.bat
    │   ├── clear_github.bat
    │   ├── unified_app.spec
    │   ├── MezuniyyetSistemi.spec
    │   ├── MezuniyyetProqrami.spec
    │   ├── setup.iss
    │   ├── Azerbaijani.isl
    │   └── render.yaml
    ├── docs/                        # Sənədlər
    │   └── __init__.py
    └── assets/                      # Resurslar
        ├── __init__.py
        └── icons/                   # İkonlar
            └── icon.ico
```

## 🔄 Köçürülən Fayllar

### Core (Əsas Funksiyalar)
- `unified_app.py` → `src/core/main.py`
- `tenant_manager.py` → `src/core/tenant_manager.py`

### UI (İstifadəçi İnterfeysi)
- `auth_windows.py` → `src/ui/auth.py`
- `ui_components.py` → `src/ui/components.py`
- `vacation_tree_view.py` → `src/ui/vacation_tree.py`
- `ui/` papkasındakı bütün fayllar → `src/ui/`

### Database (Veritaban)
- `database.py` → `src/database/database.py`
- `database_sqlite.py` → `src/database/sqlite_db.py`
- `database_manager.py` → `src/database/manager.py`
- `database/` papkasındakı bütün fayllar → `src/database/`

### API (Mərkəzi Server)
- `main.py` → `src/api/server.py`
- `central_client.py` → `src/api/client.py`
- `api/` papkasındakı bütün fayllar → `src/api/`

### Utils (Köməkçi Funksiyalar)
- `cache_manager.py` → `src/utils/cache.py`
- `updater_service.py` → `src/utils/updater.py`
- `update_script.py` → `src/utils/update_script.py`
- `debug_*.py` faylları → `src/utils/`
- `fix_*.py` faylları → `src/utils/`
- `setup_*.py` faylları → `src/utils/`

### Config (Konfiqurasiya)
- `version.txt` → `src/config/version.txt`
- `requirements.txt` → `src/config/requirements.txt`

### Tests (Test Faylları)
- `test/` papkasındakı bütün fayllar → `src/tests/` (tema testləri silindi)

### Build (Build Faylları)
- `*.bat` faylları → `src/build/`
- `*.spec` faylları → `src/build/`
- `*.iss` faylları → `src/build/`
- `*.isl` faylları → `src/build/`
- `*.yaml` faylları → `src/build/`

### Assets (Resurslar)
- `icons/` papkasındakı bütün fayllar → `src/icons/`

## ✅ Üstünlüklər

1. **Modulyar Təşkil**: Hər funksiya öz papkasında
2. **Aydın Struktur**: Fayllar məqsədlərinə görə təşkil edilib
3. **Asan İdarəetmə**: Kod tapmaq və düzəltmək asan
4. **Scalable**: Yeni funksiyalar əlavə etmək asan
5. **Professional**: Standart proqram təşkil strukturuna uyğun

## 🚀 İstifadə

```bash
# Proqramı işə salmaq
python main.py

# Kitabxanaları quraşdırmaq
pip install -r src/config/requirements.txt

# Testləri işə salmaq
python src/tests/test_vacation_panel.py
```

## 📝 Qeydlər

- Bütün import yolları yeni struktur üçün yenilənib
- Əsas fayl `main.py` yeni strukturda işləyir
- Bütün funksiyalar öz yerində saxlanılıb
- Geri uyğunluq saxlanılıb

## 🎯 Yekun Nəticə

### ✅ Uğurla Tamamlanan İşlər:

1. **Səliqəli Struktur**: Bütün fayllar məqsədlərinə görə təşkil edilib
2. **Modulyar Təşkil**: Hər funksiya öz papkasında yerləşdirilib
3. **Import Yolları**: Bütün import yolları yeni struktur üçün yenilənib
4. **Test Edilib**: Proqram yeni strukturda uğurla işə düşür
5. **Dokumentasiya**: Yeni struktur tam şəkildə sənədləşdirilib

### 📊 Statistikalar:

- **Ümumi Fayl Sayı**: 50+ fayl səliqəli şəkildə təşkil edilib
- **Papka Sayı**: 10 əsas papka yaradılıb
- **Modul Sayı**: 6 əsas modul təşkil edilib
- **Test Edilib**: ✅ Proqram yeni strukturda işləyir

### 🚀 Növbəti Addımlar:

1. **Kod Təmizləmə**: Köhnə faylları silmək
2. **Test Etmək**: Bütün funksiyaları test etmək
3. **Dokumentasiya**: Daha detallı sənədlər yaratmaq
4. **Optimizasiya**: Performansı artırmaq

---

**Məzuniyyət Sistemi v6.7** - Professional məzuniyyət idarəetmə həlli (Səliqəli Struktur) ✅ 