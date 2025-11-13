# 📧 Resend-də Domain Təsdiqləmə - Addım-Addım Təlimat

## 🎯 Məqsəd
`mezuniyyet.com` domain-ini Resend-də təsdiqləyərək email göndərməni aktivləşdirmək.

---

## 📋 Addım 1: Resend-də Domain Əlavə Edin

1. **https://resend.com** saytına daxil olun
2. Sol menyudan **"Domains"** bölməsinə keçin
3. **"Add Domain"** düyməsinə basın
4. Domain adınızı daxil edin:
   - **Format:** `mail.mezuniyyet.com` (və ya sadəcə `mezuniyyet.com`)
   - **Qeyd:** `mail.` prefiksi istifadə edin (məsələn: `mail.mezuniyyet.com`)
5. **"Add"** və ya **"Continue"** basın
6. Resend sizə DNS qeydlərini verəcək:
   - **SPF qeydi** (TXT) - məsələn: `v=spf1 include:_spf.resend.com ~all`
   - **DKIM qeydi** (TXT) - məsələn: `resend._domainkey` ilə başlayır
   - **CNAME qeydi** - məsələn: `resend` → `resend.com`
7. **Bu qeydləri kopyalayın və saxlayın!** 📝

---

## 📋 Addım 2: Namecheap-da DNS Qeydlərini Əlavə Edin

1. **https://www.namecheap.com** saytına daxil olun
2. Hesabınıza daxil olun
3. **"Domain List"** bölməsinə keçin
4. **"mezuniyyet.com"** domain-inizi tapın və üzərinə klikləyin
5. **"Advanced DNS"** sekmesinə keçin
6. **"Add New Record"** düyməsinə basın
7. Resend-dən aldığınız qeydləri əlavə edin:

### SPF qeydi (TXT):
- **Type:** `TXT Record`
- **Host:** `@` (və ya boş)
- **Value:** Resend-dən aldığınız SPF qeydi (məsələn: `v=spf1 include:_spf.resend.com ~all`)
- **TTL:** `Automatic` (və ya `3600`)
- **"Save"** basın

### DKIM qeydi (TXT):
- **Type:** `TXT Record`
- **Host:** `resend._domainkey` (və ya Resend-dən aldığınız ad)
- **Value:** Resend-dən aldığınız DKIM qeydi (uzun mətn)
- **TTL:** `Automatic` (və ya `3600`)
- **"Save"** basın

### CNAME qeydi:
- **Type:** `CNAME Record`
- **Host:** `resend` (və ya Resend-dən aldığınız ad)
- **Value:** `resend.com` (və ya Resend-dən aldığınız target)
- **TTL:** `Automatic` (və ya `3600`)
- **"Save"** basın

---

## 📋 Addım 3: Domain Təsdiqləmə

1. DNS qeydlərini əlavə etdikdən sonra **24-48 saat** gözləyin (DNS yayılması)
2. Resend dashboard-da **"Domains"** bölməsinə keçin
3. Domain-inizin yanında **"Verify"** və ya **"Check DNS"** düyməsini basın
4. Əgər bütün qeydlər düzgündürsə, domain **"Verified"** statusuna keçəcək

**Qeyd:** DNS yayılması 24-48 saat çəkə bilər. Bəzən daha tez ola bilər (bir neçə saat).

---

## 📋 Addım 4: Render.com-da Email Ünvanını Yeniləyin

1. **https://render.com** saytına gedin
2. **"mezuniyyet-serverim"** servisinizi açın
3. **"Environment"** sekmesinə keçin
4. `RESEND_FROM_EMAIL` variable-ını yeniləyin:
   - **Key:** `RESEND_FROM_EMAIL`
   - **Value:** `noreply@mail.mezuniyyet.com` (və ya domain-inizə uyğun)
   - **Qeyd:** `mail.mezuniyyet.com` domain-inizdir (Resend-də əlavə etdiyiniz)
5. **"Save Changes"** basın
6. Servisi yenidən başladın: **"Manual Deploy"** → **"Deploy latest commit"**

---

## ✅ Test Etmə

1. Domain təsdiqləndikdən sonra proqramı işə salın
2. Şifrə sıfırlama funksiyasını test edin
3. Email göndərməyə cəhd edin
4. Render.com loglarında görünəcək:
   ```
   ✅ [SERVER_API] Email Resend ilə uğurla göndərildi
   ```

---

## 🔍 Problem Həlləri

### Problem: "Domain verification failed"
**Həll:** 
- DNS qeydlərinin düzgün əlavə edildiyini yoxlayın
- DNS yayılması üçün 24-48 saat gözləyin
- Namecheap-da DNS qeydlərinin düzgün olduğunu yoxlayın

### Problem: "DNS records not found"
**Həll:** 
- DNS qeydlərinin yayılması üçün gözləyin
- Namecheap-da DNS qeydlərinin düzgün əlavə edildiyini yoxlayın
- Resend-də DNS qeydlərini yenidən yoxlayın

---

## 🎉 Hazır!

Domain təsdiqləndikdən sonra email göndərmə işləyəcək və istənilən email ünvanına göndərə biləcəksiniz!

