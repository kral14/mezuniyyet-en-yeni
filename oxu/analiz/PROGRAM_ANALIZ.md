# Məzuniyyət Sistemi v7.11 - Dərindən Təhlil

## 📋 Ümumi Məlumat

**Proqram Adı:** Məzuniyyət İdarəetmə Sistemi  
**Versiya:** v7.11  
**Dil:** Python 3.8+  
**GUI Framework:** Tkinter (ttkbootstrap dəstəyi ilə)  
**Veritabanı:** PostgreSQL (əsas), SQLite (offline dəstək)  
**Arxitektura:** Multi-tenant (çoxlu şirkət dəstəyi)

---

## 🏗️ Arxitektura və Struktur

### 1. Əsas Giriş Nöqtəsi

**Fayl:** `main.py`
- PyInstaller EXE mühitini yoxlayır
- Debug sistemini konfiqurasiya edir
- `src/core/main.py`-dəki `UnifiedApplication` sinifini işə salır
- Import yollarını dinamik şəkildə həll edir

### 2. Əsas Tətbiq Sinifi

**Fayl:** `src/core/main.py` → `UnifiedApplication` sinifi

**Əsas Funksiyalar:**
- **Tenant (Şirkət) İdarəetməsi:** Çoxlu şirkət dəstəyi
- **Giriş/Qeydiyyat Sistemi:** İstifadəçi autentifikasiyası
- **Versiya İdarəetməsi:** Avtomatik yeniləmə sistemi
- **Offline Database:** SQLite ilə offline iş rejimi
- **Debug Sistemi:** Real-time debug və log idarəetməsi

**Əsas Komponentlər:**
```python
- UnifiedApplication (tk.Tk)
  ├── Tenant Manager (şirkət idarəetməsi)
  ├── Auth System (giriş/qeydiyyat)
  ├── Main App Frame (əsas tətbiq pəncərəsi)
  ├── Update Service (yeniləmə sistemi)
  └── Debug System (debug idarəetməsi)
```

---

## 📁 Modul Strukturu

### 1. Core Modulları (`src/core/`)

#### `main.py` - Əsas Tətbiq
- **UnifiedApplication:** Ana tətbiq sinifi
- **CreateTenantWindow:** Yeni şirkət yaratma pəncərəsi
- **LoginFrame/RegisterFrame:** Giriş/qeydiyyat interfeysi
- **Şirkət seçimi və qoşulma mexanizmi**

#### `tenant_manager.py` - Şirkət İdarəetməsi
- **CentralServerClient:** Mərkəzi server ilə əlaqə
- **Tenant yaratma, axtarış, link idarəetməsi**
- **Universal link sistemi:** Hər şirkət üçün unikal link
- **Connection string hash-ləmə:** Təhlükəsizlik üçün

#### `email_service.py` - Email Xidməti
- **Şifrə sıfırlama:** Email vasitəsilə
- **Rate limiting:** Spam qarşısı
- **Server-based email:** Mərkəzi server vasitəsilə göndərmə
- **Reset kodları:** Təhlükəsiz şifrə sıfırlama

#### `real_time_notifier.py` - Real-time Bildirişlər
- **WebSocket dəstəyi:** Real-time əlaqə
- **Polling fallback:** WebSocket işləmədikdə
- **Dəyişiklik izləmə:** Məzuniyyət statusu dəyişiklikləri
- **Callback sistemi:** UI yeniləmələri üçün

---

### 2. Database Modulları (`src/database/`)

#### `database.py` - Əsas Veritabanı Əməliyyatları
- **db_connect():** PostgreSQL qoşulması
- **Connection string idarəetməsi:** Dinamik konfiqurasiya
- **İşçi məlumatları:** CRUD əməliyyatları
- **Məzuniyyət sorğuları:** Əlavə, yeniləmə, silmə

#### `vacation_queries.py` - Məzuniyyət Sorğuları
- **add_vacation():** Yeni məzuniyyət sorğusu
- **update_vacation():** Məzuniyyət yeniləmə
- **update_vacation_status():** Təsdiq/rədd
- **delete_vacation():** Məzuniyyət silmə
- **Bildiriş avtomatik yaradılması**

#### `notification_queries.py` - Bildiriş Sistemi
- **create_notification():** Yeni bildiriş
- **Bildiriş statusu:** Oxunub/oxunmayıb
- **Admin bildirişləri:** Məzuniyyət sorğuları üçün

#### `user_queries.py` - İstifadəçi Sorğuları
- **Giriş/çıxış:** Sessiya idarəetməsi
- **Şifrə idarəetməsi:** Hash, sıfırlama
- **Rol idarəetməsi:** Admin/user

#### `session_queries.py` - Sessiya İdarəetməsi
- **Sessiya yaratma:** UUID ilə
- **Sessiya izləmə:** Giriş tarixçəsi
- **Çoxlu sessiya dəstəyi**

#### `connection.py` - Veritabanı Qoşulması
- **Connection pooling:** Performans üçün
- **Connection string parsing**
- **Error handling**

#### `offline_db.py` - Offline Database
- **SQLite dəstəyi:** İnternet olmadıqda
- **Sync mexanizmi:** Online olduqda sinxronizasiya

---

### 3. UI Modulları (`src/ui/`)

#### `main_frame.py` - Əsas Pəncərə (5783 sətir!)
**Əsas Komponentlər:**
- **MainAppFrame:** Ana tətbiq çərçivəsi
- **Dashboard:** Statistika və təqvim
- **İşçi idarəetməsi:** Əlavə, redaktə, silmə
- **Məzuniyyət idarəetməsi:** Sorğu, təsdiq, rədd
- **Bildirişlər:** Real-time bildirişlər
- **Profil:** İstifadəçi məlumatları

**Əsas Funksiyalar:**
```python
- create_main_layout()      # UI struktur yaradır
- create_views()            # Fərqli görünüşlər (dashboard, employees, etc.)
- load_and_refresh_data()   # Məlumat yükləmə
- show_view()               # Görünüş dəyişdirmə
- setup_left_panel()        # Sol menyu
- setup_navbar()            # Navbar
```

#### `auth.py` - Autentifikasiya
- **LoginFrame:** Giriş pəncərəsi
- **RegisterFrame:** Qeydiyyat pəncərəsi
- **Azərbaycan hərfləri dəstəyi:** Xüsusi klaviatura kombinasiyaları
- **Şifrə sıfırlama:** Email vasitəsilə

#### `vacation_tree.py` - Məzuniyyət Ağacı
- **VacationTreeView:** Məzuniyyətlərin ağac görünüşü
- **Status dəyişdirmə:** Təsdiq/rədd
- **Filtri və axtarış**

#### `dashboard_calendar_frame.py` - Dashboard Təqvim
- **Təqvim görünüşü:** Məzuniyyətlərin təqvimdə göstərilməsi
- **HTML/JavaScript:** İnteraktiv təqvim

#### `employee_form_window.py` - İşçi Formu
- **Yeni işçi əlavə etmə**
- **İşçi redaktə etmə**
- **Məlumat validasiyası**

#### `employee_detail_frame.py` - İşçi Detalları
- **İşçi məlumatlarının detallı görünüşü**
- **Məzuniyyət tarixçəsi**

#### `notifications_window.py` - Bildirişlər
- **Bildiriş siyahısı**
- **Oxunub/oxunmayıb statusu**
- **Real-time yeniləmə**

#### `user_management_window.py` - İstifadəçi İdarəetməsi
- **İstifadəçi siyahısı** (yalnız admin)
- **Rol dəyişdirmə**
- **İstifadəçi silmə**

#### `archive_window.py` - Arxiv
- **Arxivə salınmış məzuniyyətlər**
- **Axtarış və filtri**

#### `components.py` - UI Komponentləri
- **CustomDateEntry:** Xüsusi tarix girişi
- **VacationPanel:** Məzuniyyət paneli
- **Tooltip:** Köməkçi məlumatlar

---

### 4. Utils Modulları (`src/utils/`)

#### `debug_manager.py` - Debug İdarəetməsi
- **Debug pəncərəsi:** Real-time log görünüşü
- **Kategoriyalı loglar:** takvim, animasiya, database, ui, etc.
- **Print intercept:** Konsol çıxışını yönləndirmə

#### `updater.py` - Yeniləmə Sistemi
- **Versiya yoxlama:** Veritabanı və GitHub-dan
- **Avtomatik yeniləmə:** Setup faylı endirmə
- **Progress göstəricisi**

#### `cache.py` - Cache Sistemi
- **Məlumat cache-ləmə:** Performans üçün
- **Cache invalidation:** Dəyişikliklərdən sonra

#### `log_helper.py` - Log İdarəetməsi
- **Log faylları:** Tarixçə ilə
- **Database logging:** Logları veritabanına yazma
- **Log arxivləmə**

#### `realtime_debug.py` - Real-time Debug
- **Signal izləmə:** Signal göndərmə/qəbul etmə
- **Performance monitoring:** Performans ölçmə
- **Network operations:** Şəbəkə əməliyyatları

#### `print_service.py` - Çap Xidməti
- **Məzuniyyət çapı:** PDF və ya çap
- **Print preview:** Önizləmə

#### `performance_monitor.py` - Performans Monitoru
- **İşləmə vaxtı ölçmə**
- **Bottleneck aşkarlama**

---

## 🔄 İş Axını (Workflow)

### 1. Proqram Başlatma
```
main.py
  └─> UnifiedApplication.__init__()
      ├─> Offline DB init
      ├─> Debug system init
      ├─> Tenant selection/creation
      └─> Login/Register
          └─> MainAppFrame
```

### 2. Məzuniyyət Sorğusu Prosesi
```
İşçi məzuniyyət sorğusu göndərir
  └─> add_vacation() (vacation_queries.py)
      ├─> Database-ə yazılır (status: 'pending')
      ├─> Adminlərə bildiriş göndərilir
      └─> Real-time signal göndərilir
          └─> Admin UI-də bildiriş görünür
              └─> Admin təsdiq/rədd edir
                  └─> update_vacation_status()
                      ├─> Status yenilənir
                      ├─> İşçiyə bildiriş göndərilir
                      └─> Real-time signal
```

### 3. Real-time Bildiriş Sistemi
```
RealTimeNotifier başladılır
  ├─> WebSocket qoşulması cəhd edilir
  │   └─> Uğurlu: WebSocket loop
  └─> Uğursuz: Polling loop (1 saniyədə bir)
      └─> Dəyişiklik aşkar edilir
          └─> Callback çağırılır
              └─> UI yenilənir
```

---

## 🔐 Təhlükəsizlik

### 1. Şifrə İdarəetməsi
- **bcrypt hashing:** Şifrələr hash edilir
- **App password:** Email üçün (server-də)
- **Reset kodları:** Təhlükəsiz şifrə sıfırlama

### 2. Sessiya İdarəetməsi
- **UUID sessiya ID-ləri:** Unikal sessiyalar
- **Sessiya tarixçəsi:** Giriş/çıxış izləmə
- **Çoxlu sessiya dəstəyi:** Eyni istifadəçi bir neçə cihazdan

### 3. Connection String
- **Hash-ləmə:** Connection string hash edilir
- **Təhlükəsiz saxlanma:** Log-larda göstərilmir
- **Tenant izolyasiyası:** Hər şirkət öz bazası ilə

---

## 📊 Veritabanı Strukturu

### Əsas Cədvəllər:
1. **employees** - İşçilər
   - id, name, email, role, department, position, etc.

2. **vacations** - Məzuniyyətlər
   - id, employee_id, start_date, end_date, status, note, created_at

3. **notifications** - Bildirişlər
   - id, recipient_id, message, related_vacation_id, is_read, created_at

4. **sessions** - Sessiyalar
   - id, user_id, session_id, login_time, logout_time

5. **login_history** - Giriş Tarixçəsi
   - id, user_id, login_time, logout_time, ip_address

---

## 🚀 Xüsusiyyətlər

### 1. Multi-Tenant Sistemi
- **Çoxlu şirkət dəstəyi:** Hər şirkət öz bazası ilə
- **Universal link:** Hər şirkət üçün unikal link
- **Mərkəzi server:** Tenant idarəetməsi üçün

### 2. Real-time Bildirişlər
- **WebSocket dəstəyi:** Real-time əlaqə
- **Polling fallback:** WebSocket işləmədikdə
- **Dərhal yeniləmə:** Status dəyişiklikləri

### 3. Offline Dəstək
- **SQLite offline DB:** İnternet olmadıqda
- **Sync mexanizmi:** Online olduqda sinxronizasiya

### 4. Debug Sistemi
- **Real-time debug pəncərəsi**
- **Kategoriyalı loglar**
- **Performance monitoring**

### 5. Avtomatik Yeniləmə
- **Versiya yoxlama:** Veritabanı və GitHub-dan
- **Avtomatik endirmə:** Setup faylı
- **Progress göstəricisi**

### 6. Azərbaycan Dili Dəstəyi
- **Azərbaycan hərfləri:** Xüsusi klaviatura kombinasiyaları
- **Unicode dəstəyi:** Düzgün encoding

---

## 🎨 UI/UX Xüsusiyyətləri

### 1. Modern İnterfeys
- **ttkbootstrap:** Modern UI komponentləri
- **Responsive dizayn:** Fərqli ekran ölçüləri
- **İkonlar:** PNG ikonlar

### 2. Animasiyalar
- **Loading animasiyaları:** GIF və JSON
- **Smooth transitions:** UI keçidləri

### 3. Təqvim Görünüşü
- **HTML/JavaScript təqvim:** İnteraktiv
- **Məzuniyyət göstərmə:** Təqvimdə vizual

### 4. Print Preview
- **Çap önizləməsi:** PDF və ya çap
- **Formatlaşdırma:** Professional görünüş

---

## 🔧 Konfiqurasiya

### 1. Tenant Settings
**Fayl:** `tenant_settings.json`
```json
{
  "tenant_id": "uuid",
  "company_name": "Şirkət adı"
}
```

### 2. Version Management
**Fayl:** `version_management/versions.json`
- Versiya tarixçəsi
- Qeydlər və fayl sayı

### 3. Debug Settings
**Fayl:** `debug_settings.json`
- Debug kategoriyaları
- Log səviyyələri

---

## 📈 Performans Optimallaşdırmaları

### 1. Lazy Loading
- **UI komponentləri:** Lazım olduqda yüklənir
- **Məlumat yükləmə:** Asinxron

### 2. Cache Sistemi
- **Məlumat cache-ləmə:** Tez-tez istifadə olunan məlumatlar
- **Cache invalidation:** Dəyişikliklərdən sonra

### 3. Connection Pooling
- **Veritabanı bağlantıları:** Pool idarəetməsi
- **Resource management:** Səmərəli istifadə

### 4. Asinxron Əməliyyatlar
- **Threading:** UI bloklanmasının qarşısı
- **Background tasks:** Arxa planda işlər

---

## 🐛 Debug və Logging

### 1. Debug Kategoriyaları
- `takvim` - Təqvim əməliyyatları
- `animasiya` - Animasiyalar
- `database` - Veritabanı əməliyyatları
- `ui` - UI yeniləmələri
- `vacation` - Məzuniyyət əməliyyatları
- `employee` - İşçi əməliyyatları
- `signal` - Signal sistemi
- `performance` - Performans ölçmələri
- `umumi` - Ümumi məlumatlar

### 2. Log Faylları
- **Timestamp ilə:** Hər sessiya üçün ayrı log
- **Database logging:** Logları veritabanına yazma
- **Log arxivləmə:** Köhnə logların arxivlənməsi

---

## 🔄 Versiya İdarəetməsi

### Version Manager
**Fayl:** `version_management/version_manager.py`
- **Versiya yaratma:** Zip faylı ilə
- **Versiya siyahısı:** Mövcud versiyalar
- **Versiya silmə/kopyalama:** İdarəetmə

---

## 📦 Build və Deployment

### 1. PyInstaller
- **EXE yaratma:** Windows üçün
- **Resource bundling:** İkonlar və fayllar

### 2. Setup Scripts
**Papka:** `setup etmek/`
- **run_build.bat:** Build prosesi
- **create_setup.bat:** Installer yaratma
- **setup.iss:** Inno Setup konfiqurasiyası

---

## 🎯 Əsas Qüvvətli Tərəflər

1. ✅ **Modulyar struktur:** Aydın kod təşkili
2. ✅ **Multi-tenant:** Çoxlu şirkət dəstəyi
3. ✅ **Real-time:** WebSocket və polling
4. ✅ **Offline dəstək:** SQLite ilə
5. ✅ **Debug sistemi:** Real-time monitoring
6. ✅ **Təhlükəsizlik:** Hash, sessiya idarəetməsi
7. ✅ **Azərbaycan dili:** Tam dəstək
8. ✅ **Modern UI:** ttkbootstrap ilə

---

## ⚠️ Potensial Təkmilləşdirmələr

1. **Unit testlər:** Test coverage artırılması
2. **API dokumentasiyası:** Swagger/OpenAPI
3. **Docker dəstəyi:** Containerization
4. **CI/CD pipeline:** Avtomatik build/deploy
5. **Monitoring:** Production monitoring
6. **Error tracking:** Sentry və ya bənzəri
7. **Performance profiling:** Daha dərin analiz

---

## 📝 Nəticə

Bu proqram **professional səviyyədə** hazırlanmış, **modulyar struktur**a malik, **multi-tenant** məzuniyyət idarəetmə sistemidir. Real-time bildirişlər, offline dəstək, debug sistemi və modern UI ilə tam funksional həlldir.

**Kod keyfiyyəti:** Yüksək  
**Arxitektura:** Modulyar və genişləndirilə bilən  
**Təhlükəsizlik:** Bcrypt, sessiya idarəetməsi, hash-ləmə  
**Performans:** Cache, lazy loading, connection pooling

---

**Təhlil tarixi:** 2024  
**Versiya:** v7.11

