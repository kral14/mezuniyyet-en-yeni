# 🌐 Pulsuz Domain Quraşdırması - Freenom

## 🎯 Məqsəd
Resend-də email göndərmək üçün domain təsdiqləmək lazımdır. Freenom-dan pulsuz domain əldə edə bilərsiniz.

---

## 📋 Addım 1: Freenom-da Domain Qeydiyyatı

1. **https://www.freenom.com** saytına gedin
2. **"Register a New Domain"** və ya **"Services"** → **"Register a New Domain"** bölməsinə keçin
3. İstədiyiniz domain adını yazın (məsələn: `mezuniyyet` və ya `vacation`)
4. **"Check Availability"** basın
5. Mövcud pulsuz domain uzantılarını seçin:
   - `.tk` (Tokelau) - **Tövsiyə olunur**
   - `.ml` (Mali)
   - `.cf` (Central African Republic)
   - `.gq` (Equatorial Guinea)
   - `.ga` (Gabon)
6. Domain mövcuddursa, **"Get it now!"** və ya **"Add to Cart"** basın
7. **"Checkout"** basın
8. Qeydiyyatdan keçin:
   - Email: `vacationseasonplans@gmail.com`
   - Şifrə: Güclü şifrə yaradın
   - **Qeyd:** Telefon nömrəsi və ödəniş kartı tələb edilmir! ✅
9. Email-də təsdiq linkinə basın
10. **"Complete Order"** basın (pulsuzdur)

**Qeyd:** Domain qeydiyyatı 1 il üçündür və pulsuz yenilənə bilər.

---

## 📋 Addım 2: DNS Qeydlərini Təyin Etmək Üçün Hazırlaşın

1. Freenom-da domain-inizi açın
2. **"Manage Domain"** → **"Manage Freenom DNS"** bölməsinə keçin
3. Burada DNS qeydlərini əlavə edəcəksiniz (Addım 4-də)

---

## 📋 Addım 3: Resend-də Domain Əlavə Edin

1. **https://resend.com** saytına daxil olun
2. **"Domains"** bölməsinə keçin
3. **"Add Domain"** basın
4. Domain adınızı daxil edin:
   - **Format:** `mail.mezuniyyet.tk` (və ya domain-inizə uyğun)
   - **Qeyd:** `mail.` prefiksi istifadə edin (məsələn: `mail.mezuniyyet.tk`)
5. **"Add"** basın
6. Resend sizə DNS qeydlərini verəcək:
   - **SPF qeydi** (TXT) - məsələn: `v=spf1 include:_spf.resend.com ~all`
   - **DKIM qeydi** (TXT) - məsələn: `resend._domainkey` ilə başlayır
   - **CNAME qeydi** - məsələn: `resend` → `resend.com`
7. Bu qeydləri kopyalayın və saxlayın

---

## 📋 Addım 4: DNS Qeydlərini Freenom-da Əlavə Edin

1. Freenom-da domain-inizi açın
2. **"Manage Domain"** → **"Manage Freenom DNS"** bölməsinə keçin
3. **"Add Record"** və ya **"Add New Record"** basın
4. Resend-dən aldığınız qeydləri əlavə edin:

### SPF qeydi (TXT):
- **Type:** `TXT`
- **Name:** `@` (və ya boş)
- **TTL:** `3600`
- **Target:** Resend-dən aldığınız SPF qeydi (məsələn: `v=spf1 include:_spf.resend.com ~all`)

### DKIM qeydi (TXT):
- **Type:** `TXT`
- **Name:** `resend._domainkey` (və ya Resend-dən aldığınız ad)
- **TTL:** `3600`
- **Target:** Resend-dən aldığınız DKIM qeydi (uzun mətn)

### CNAME qeydi:
- **Type:** `CNAME`
- **Name:** `resend` (və ya Resend-dən aldığınız ad)
- **TTL:** `3600`
- **Target:** `resend.com` (və ya Resend-dən aldığınız target)

5. Hər qeydi əlavə etdikdən sonra **"Save"** basın

---

## 📋 Addım 5: Domain Təsdiqləmə

1. DNS qeydlərini əlavə etdikdən sonra **24-48 saat** gözləyin (DNS yayılması)
2. Resend dashboard-da **"Domains"** bölməsinə keçin
3. Domain-inizin yanında **"Verify"** və ya **"Check DNS"** düyməsini basın
4. Əgər bütün qeydlər düzgündürsə, domain **"Verified"** statusuna keçəcək

**Qeyd:** DNS yayılması 24-48 saat çəkə bilər. Bəzən daha tez ola bilər (bir neçə saat).

---

## 📋 Addım 6: Render.com-da Email Ünvanını Yeniləyin

1. **https://render.com** saytına gedin
2. **"mezuniyyet-serverim"** servisinizi açın
3. **"Environment"** sekmesinə keçin
4. `RESEND_FROM_EMAIL` variable-ını yeniləyin:
   - **Key:** `RESEND_FROM_EMAIL`
   - **Value:** `noreply@mail.mezuniyyet.tk` (və ya domain-inizə uyğun)
   - **Qeyd:** `mail.mezuniyyet.tk` domain-inizdir (Resend-də əlavə etdiyiniz)
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
- Freenom-da DNS qeydlərinin düzgün olduğunu yoxlayın

### Problem: "DNS records not found"
**Həll:** 
- DNS qeydlərinin yayılması üçün gözləyin
- Freenom-da DNS qeydlərinin düzgün əlavə edildiyini yoxlayın
- Resend-də DNS qeydlərini yenidən yoxlayın

### Problem: "Domain already exists"
**Həll:** 
- Başqa domain adı seçin
- Və ya Freenom-da mövcud domain-inizi istifadə edin

---

## 💡 Tövsiyələr

1. **Domain adı:** Qısa və yadda qalan ad seçin (məsələn: `mezuniyyet.tk`)
2. **DNS yayılması:** 24-48 saat gözləyin, bəzən daha tez ola bilər
3. **Test:** Domain təsdiqləndikdən sonra test edin
4. **Yeniləmə:** Freenom-da domain-i pulsuz yeniləyə bilərsiniz (1 il üçün)

---

## 🎉 Hazır!

Domain təsdiqləndikdən sonra email göndərmə işləyəcək və istənilən email ünvanına göndərə biləcəksiniz!

