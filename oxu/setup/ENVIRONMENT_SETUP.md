# Render.com Environment Variable-ları Quraşdırması

## 📋 Lazım Olan Environment Variable-lar

### 1. **SMTP_SERVER**
- **Dəyər:** `smtp.gmail.com`
- **Təsvir:** Gmail SMTP server ünvanı

### 2. **SMTP_PORT**
- **Dəyər:** `587`
- **Təsvir:** Gmail SMTP portu (TLS üçün)

### 3. **SENDER_EMAIL**
- **Dəyər:** `vacationseasonplans@gmail.com`
- **Təsvir:** Email göndərən ünvan

### 4. **APP_PASSWORD** ⚠️ TƏHLÜKƏSİZLİK
- **Dəyər:** Gmail App Password (16 simvol)
- **Təsvir:** Gmail App Password (təhlükəsizlik üçün manual təyin edin)
- **Qeyd:** Bu dəyəri Render dashboard-dan manual təyin edin, kodda saxlamayın!

---

## 🚀 Render.com-da Quraşdırma

### Addım 1: Render Dashboard-a Daxil Olun
1. https://render.com saytına gedin
2. Hesabınıza daxil olun

### Addım 2: Servisinizi Tapın
1. Dashboard-da servisinizi tapın
2. Servisin üzərinə klikləyin

### Addım 3: Environment Variable-ları Əlavə Edin
1. Sol menyudan **"Environment"** sekmesinə keçin
2. **"Add Environment Variable"** düyməsinə basın
3. Aşağıdakı variable-ları əlavə edin:

```
SMTP_SERVER = smtp.gmail.com
SMTP_PORT = 587
SENDER_EMAIL = vacationseasonplans@gmail.com
APP_PASSWORD = your-gmail-app-password-here
```

### Addım 4: Servisi Yenidən Başladın
1. Variable-ları əlavə etdikdən sonra **"Manual Deploy"** → **"Deploy latest commit"** basın
2. Və ya servis avtomatik yenidən başlayacaq

---

## 🔐 Gmail App Password Almaq

### Addım 1: Gmail Hesabında 2FA Aktivləşdirin
1. https://myaccount.google.com/security saytına gedin
2. "2-Step Verification" aktivləşdirin

### Addım 2: App Password Yaradın
1. https://myaccount.google.com/apppasswords saytına gedin
2. "Select app" → "Other (Custom name)"
3. Ad: "Mezuniyyet Sistemi Server"
4. "Generate" basın
5. **16 simvoldan ibarət şifrəni kopyalayın**

### Addım 3: Render-də Təyin Edin
1. Render dashboard-da `APP_PASSWORD` variable-ına bu şifrəni yazın
2. Save edin

---

## ✅ Yoxlama

### Test Endpoint:
```bash
curl -X POST https://mezuniyyet-serverim.onrender.com/api/email/send-reset \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "employee_name": "Test İstifadəçi"
  }'
```

### Uğurlu Cavab:
```json
{
  "success": true,
  "message": "Email uğurla göndərildi!",
  "reset_code": "123456"
}
```

---

## ⚠️ Təhlükəsizlik Qeydləri

1. **APP_PASSWORD** heç vaxt kodda saxlamayın
2. Yalnız Render dashboard-dan təyin edin
3. Şifrəni heç kimə verməyin
4. Şifrə oğurlanarsa, dərhal yenisini yaradın

---

## 🔧 Xəta Həlli

### Problem: Email göndərilmir
**Həll:**
- APP_PASSWORD düzgün təyin edilib yoxla
- Gmail App Password-in aktiv olduğunu yoxla
- Render log-larına bax: Dashboard → Logs

### Problem: SMTP Authentication Error
**Həll:**
- APP_PASSWORD düzgündürmü yoxla
- Gmail hesabında 2FA aktivdir yoxla
- Yeni App Password yaradın

---

## 📝 Qeyd

Environment variable-ları dəyişdikdən sonra servis avtomatik yenidən başlayacaq. Bu 1-2 dəqiqə çəkə bilər.

