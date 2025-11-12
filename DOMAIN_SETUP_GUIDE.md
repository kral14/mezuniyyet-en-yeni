# 🌐 Domain Alması və Resend-də Təsdiqləmə - Addım-Addım Təlimat

## 🎯 Məqsəd
`.com` domain alıb Resend-də təsdiqləyərək email göndərməni aktivləşdirmək.

---

## 📋 Addım 1: Domain Alın

### Seçim 1: Namecheap (Tövsiyə olunur)
1. **https://www.namecheap.com** saytına gedin
2. **"Sign Up"** basın və hesab yaradın
3. Domain axtarış çubuğuna istədiyiniz adı yazın (məsələn: `mezuniyyet`)
4. **"Search"** basın
5. `.com` domain-i seçin və **"Add to Cart"** basın
6. **"View Cart"** → **"Checkout"** basın
7. Ödəniş edin:
   - Qiymət: ~$10-12/il (təxminən 20-24 AZN)
   - Kredit kartı və ya PayPal ilə ödəniş edə bilərsiniz

### Seçim 2: GoDaddy
1. **https://www.godaddy.com** saytına gedin
2. Domain axtarış çubuğuna istədiyiniz adı yazın
3. `.com` domain-i seçin və **"Add to Cart"** basın
4. Qeydiyyatdan keçin və ödəniş edin
5. Qiymət: ~$12-15/il

### Seçim 3: Cloudflare Registrar
1. **https://www.cloudflare.com/products/registrar/** saytına gedin
2. Domain axtarış edin və alın
3. Qiymət: ~$9-10/il (at-cost pricing)

---

## 📋 Addım 2: Resend-də Domain Əlavə Edin

1. **https://resend.com** saytına daxil olun
2. **"Domains"** bölməsinə keçin
3. **"Add Domain"** basın
4. Domain adınızı daxil edin:
   - **Format:** `mail.mezuniyyet.com` (və ya `mezuniyyet.com`)
   - **Qeyd:** `mail.` prefiksi istifadə edin (məsələn: `mail.mezuniyyet.com`)
5. **"Add"** basın
6. Resend sizə DNS qeydlərini verəcək:
   - **SPF qeydi** (TXT) - məsələn: `v=spf1 include:_spf.resend.com ~all`
   - **DKIM qeydi** (TXT) - məsələn: `resend._domainkey` ilə başlayır
   - **CNAME qeydi** - məsələn: `resend` → `resend.com`
7. Bu qeydləri kopyalayın və saxlayın

---

## 📋 Addım 3: DNS Qeydlərini Domain Provayderinizdə Əlavə Edin

### Namecheap üçün:
1. Namecheap-da domain-inizi açın
2. **"Advanced DNS"** bölməsinə keçin
3. **"Add New Record"** basın
4. Resend-dən aldığınız qeydləri əlavə edin:

#### SPF qeydi (TXT):
- **Type:** `TXT Record`
- **Host:** `@` (və ya boş)
- **Value:** Resend-dən aldığınız SPF qeydi (məsələn: `v=spf1 include:_spf.resend.com ~all`)
- **TTL:** `Automatic` (və ya `3600`)
- **"Save"** basın

#### DKIM qeydi (TXT):
- **Type:** `TXT Record`
- **Host:** `resend._domainkey` (və ya Resend-dən aldığınız ad)
- **Value:** Resend-dən aldığınız DKIM qeydi (uzun mətn)
- **TTL:** `Automatic` (və ya `3600`)
- **"Save"** basın

#### CNAME qeydi:
- **Type:** `CNAME Record`
- **Host:** `resend` (və ya Resend-dən aldığınız ad)
- **Value:** `resend.com` (və ya Resend-dən aldığınız target)
- **TTL:** `Automatic` (və ya `3600`)
- **"Save"** basın

### GoDaddy üçün:
1. GoDaddy-da domain-inizi açın
2. **"DNS"** bölməsinə keçin
3. **"Add"** basın və Resend-dən aldığınız qeydləri əlavə edin

### Cloudflare üçün:
1. Cloudflare-da domain-inizi açın
2. **"DNS"** bölməsinə keçin
3. **"Add record"** basın və Resend-dən aldığınız qeydləri əlavə edin

---

## 📋 Addım 4: Domain Təsdiqləmə

1. DNS qeydlərini əlavə etdikdən sonra **24-48 saat** gözləyin (DNS yayılması)
2. Resend dashboard-da **"Domains"** bölməsinə keçin
3. Domain-inizin yanında **"Verify"** və ya **"Check DNS"** düyməsini basın
4. Əgər bütün qeydlər düzgündürsə, domain **"Verified"** statusuna keçəcək

**Qeyd:** DNS yayılması 24-48 saat çəkə bilər. Bəzən daha tez ola bilər (bir neçə saat).

---

## 📋 Addım 5: Render.com-da Email Ünvanını Yeniləyin

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
- Domain provayderinizdə DNS qeydlərinin düzgün olduğunu yoxlayın

### Problem: "DNS records not found"
**Həll:** 
- DNS qeydlərinin yayılması üçün gözləyin
- Domain provayderinizdə DNS qeydlərinin düzgün əlavə edildiyini yoxlayın
- Resend-də DNS qeydlərini yenidən yoxlayın

---

## 💰 Xərclər

- **Domain (.com):** ~$10-12/il (təxminən 20-24 AZN)
- **Hosting (Render.com Free):** $0/il (pulsuz)
- **Email (Resend Free):** $0/il (pulsuz)
- **Ümumi:** ~$10-12/il (yalnız domain)

---

## 🎉 Hazır!

Domain təsdiqləndikdən sonra email göndərmə işləyəcək və istənilən email ünvanına göndərə biləcəksiniz!

