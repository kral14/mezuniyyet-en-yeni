# 🔒 Təhlükəsizlik Təlimatları

## ⚠️ Vacib Təhlükəsizlik Qaydaları

### 1. **Real Connection String-lər**
- ❌ **Heç vaxt** real veritaban connection string-lərini kodda saxlamayın
- ✅ **Həmişə** tenant sistemi və ya konfiqurasiya fayllarından istifadə edin
- ✅ Connection string-lər `.gitignore` faylında qeyd olunmalıdır

### 2. **Email Konfiqurasiyası**
- ❌ **Heç vaxt** Gmail App Password-i kodda saxlamayın
- ✅ `email_config.json` faylında saxlayın və `.gitignore`-a əlavə edin
- ✅ App Password-i heç kimə verməyin

### 3. **Test Məlumatları**
- ❌ **Heç vaxt** real şifrələri test məlumatları kimi istifadə etməyin
- ✅ Test məqsədilə sadə şifrələr istifadə edin (admin123, user123)
- ✅ İstifadə etməzdən əvvəl şifrələri dəyişdirin

### 4. **Git Təhlükəsizliyi**
- ❌ **Heç vaxt** təhlükəsizlik fayllarını git-ə commit etməyin
- ✅ `.gitignore` faylını düzgün konfiqurasiya edin
- ✅ Commit etməzdən əvvəl `git status` ilə yoxlayın

## 📁 Təhlükəsizlik Faylları

### `.gitignore`-a əlavə edilən fayllar:
```
# Təhlükəsizlik faylları
email_config.json
connection_settings.json
*.key
*.pem
*.p12
*.pfx

# Veritaban faylları
*.db
*.sqlite
*.sqlite3

# Log faylları
*.log
debug_logs/
```

## 🔧 Konfiqurasiya Faylları

### 1. Email Konfiqurasiyası (`email_config.json`)
```json
{
    "app_password": "your-gmail-app-password",
    "sender_email": "your-email@gmail.com",
    "instructions": "Gmail App Password-i buraya yazın"
}
```

### 2. Connection Settings (`connection_settings.json`)
```json
{
    "connection_string": "postgresql://user:pass@host:port/db",
    "tenant_id": "your-tenant-id",
    "company_name": "Your Company"
}
```

## 🛡️ Təhlükəsizlik Yoxlaması

### Commit etməzdən əvvəl yoxlayın:
1. `git status` - hansı faylların commit olunacağını görün
2. Təhlükəsizlik fayllarının siyahıda olmadığını təsdiqləyin
3. Real connection string-lərin kodda olmadığını yoxlayın
4. Real şifrələrin kodda olmadığını yoxlayın

### Avtomatik yoxlama:
```bash
# Təhlükəsizlik fayllarını axtarın
grep -r "postgresql://" src/
grep -r "password" src/
grep -r "app_password" src/
```

## 🚨 Təcili Tədbirlər

### Əgər təhlükəsizlik faylı git-ə əlavə olunubsa:
1. Dərhal şifrələri dəyişdirin
2. Git tarixindən faylı silin: `git filter-branch`
3. `.gitignore` faylını yeniləyin
4. Təhlükəsizlik auditini keçirin

## 📞 Dəstək

Təhlükəsizlik məsələləri üçün:
- Sistem administratoru ilə əlaqə saxlayın
- Təhlükəsizlik auditini keçirin
- Şifrələri dəyişdirin

---

**⚠️ Diqqət:** Bu təlimatları həmişə tətbiq edin və təhlükəsizlik məsələlərini ciddi qəbul edin!

