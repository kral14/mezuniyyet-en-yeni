# Gmail SMTP Quraşdırması - Şifrə Sıfırlama Sistemi

## 📧 Gmail SMTP Konfiqurasiyası

### 1. Gmail Hesabı Hazırlama

#### 1.1 Gmail hesabı yaradın (əgər yoxdursa)
- [Gmail](https://gmail.com) saytına gedin
- Yeni hesab yaradın

#### 1.2 2FA (İkiqat Təsdiq) Aktivləşdirin
1. Gmail hesabınıza daxil olun
2. [Google Hesabı Təhlükəsizlik](https://myaccount.google.com/security) səhifəsinə gedin
3. "2-Step Verification" bölməsini tapın
4. "Get started" düyməsinə basın
5. Telefon nömrənizi daxil edin və təsdiq edin

#### 1.3 App Password Yaradın
1. [Google Hesabı Təhlükəsizlik](https://myaccount.google.com/security) səhifəsinə gedin
2. "App passwords" bölməsini tapın
3. "Select app" dropdown-dan "Other (Custom name)" seçin
4. Ad olaraq "Mezuniyyet Sistemi" yazın
5. "Generate" düyməsinə basın
6. **16 simvoldan ibarət şifrəni kopyalayın və saxlayın**

### 2. Kod Konfiqurasiyası

#### 2.1 Email Service Faylını Yeniləyin
`src/core/email_service.py` faylında aşağıdakı məlumatları dəyişin:

```python
class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "your-email@gmail.com"  # Gmail hesabınızı buraya yazın
        self.app_password = "your-app-password"     # App Password buraya yazın
```

#### 2.2 Dəyişdiriləcək Məlumatlar:
- `your-email@gmail.com` → Sizin Gmail ünvanınız
- `your-app-password` → 1.3 addımında aldığınız 16 simvoldan ibarət App Password

### 3. Test Etmə

#### 3.1 Test Email Göndərmə
```python
from core.email_service import email_service

# Test email göndər
success, message = email_service.send_reset_email("test@example.com", "Test İşçi")
print(f"Email göndərilməsi: {success}")
print(f"Mesaj: {message}")
```

#### 3.2 Uğurlu Test Nəticəsi:
```
Email göndərilməsi: True
Mesaj: Email uğurla göndərildi!
```

### 4. Təhlükəsizlik Tövsiyələri

#### 4.1 App Password Təhlükəsizliyi
- ✅ App Password-i heç kimə verməyin
- ✅ Kod fayllarında saxlamayın
- ✅ Mühüm fayllarda şifrələyin

#### 4.2 Email Limitləri
- Gmail: Günlük 500 email
- Test üçün kifayətdir
- Daha çox lazımdırsa ödənişli xidmət istifadə edin

### 5. Xəta Həlləri

#### 5.1 "Authentication failed" Xətası
**Səbəb:** Yanlış App Password
**Həll:** Yeni App Password yaradın

#### 5.2 "SMTP server connection failed" Xətası
**Səbəb:** İnternet bağlantısı problemi
**Həll:** İnternet bağlantınızı yoxlayın

#### 5.3 "Daily sending quota exceeded" Xətası
**Səbəb:** Günlük limit aşıldı
**Həll:** Sabah gözləyin və ya ödənişli xidmətə keçin

### 6. İstifadə Təlimatı

#### 6.1 İşçi Şifrə Sıfırlama
1. İşçi "Şifrəmi Unutdum" düyməsinə basır
2. Email ünvanını daxil edir
3. 6 rəqəmli kod email-ə göndərilir
4. Kodu daxil edir
5. Yeni şifrə təyin edir

#### 6.2 Admin Təhlükəsizlik
- Admin bütün şifrə dəyişikliklərini görə bilər
- Email göndərilməsi log-lanır
- Təsdiq kodları 10 dəqiqə etibarlıdır

### 7. Dəstək

Əgər problem yaşayırsınızsa:
1. Gmail təhlükəsizlik tənzimləmələrini yoxlayın
2. App Password-in düzgün olduğunu təsdiq edin
3. İnternet bağlantınızı yoxlayın
4. Log fayllarını yoxlayın

---

**Qeyd:** Bu sistem tamamilə ödənişsizdir və Gmail-in standart SMTP xidmətindən istifadə edir.