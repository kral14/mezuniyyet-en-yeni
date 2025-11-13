# 📧 Resend Domain Quraşdırması - Pulsuz Domain

## 🎯 Problem
Resend-də email göndərmək üçün domain təsdiqləmək lazımdır. Öz domain-iniz yoxdursa, iki seçim var:

---

## ✅ Seçim 1: Resend-in Default Domain-i (Ən Asan)

**Qeyd:** Resend-in default domain-i (`onboarding@resend.dev`) **yalnız test üçündür** və məhdud sayda email göndərə bilər.

### Addımlar:
1. Render.com-da `RESEND_FROM_EMAIL` variable-ı artıq təyin edilib: `onboarding@resend.dev`
2. Deployment tamamlandıqdan sonra test edin
3. Email `onboarding@resend.dev` ünvanından gələcək

**Üstünlükləri:**
- ✅ Heç bir quraşdırma tələb etmir
- ✅ Dərhal işləyir
- ✅ Pulsuzdur

**Məhdudiyyətləri:**
- ⚠️ Yalnız test üçündür
- ⚠️ Məhdud sayda email göndərə bilər
- ⚠️ Email ünvanı `onboarding@resend.dev` olacaq (öz adınız deyil)

---

## 🌐 Seçim 2: Pulsuz Domain (Freenom)

Freenom vasitəsilə pulsuz domain əldə edə bilərsiniz.

### Addım 1: Freenom-da Domain Qeydiyyatı

1. **https://www.freenom.com** saytına gedin
2. **"Register a New Domain"** bölməsinə keçin
3. İstədiyiniz domain adını yazın (məsələn: `mezuniyyet`)
4. Mövcud pulsuz domain uzantılarını seçin:
   - `.tk` (Tokelau)
   - `.ml` (Mali)
   - `.cf` (Central African Republic)
   - `.gq` (Equatorial Guinea)
   - `.ga` (Gabon)
5. **"Check Availability"** basın
6. Domain mövcuddursa, **"Get it now!"** basın
7. Qeydiyyatdan keçin (email və şifrə ilə)
8. Domain-i **"Add to Cart"** və **"Checkout"** basın
9. **"Complete Order"** basın (pulsuzdur)

**Qeyd:** Freenom-da qeydiyyat zamanı telefon nömrəsi və ödəniş kartı tələb edilmir, amma email təsdiqləməsi lazımdır.

### Addım 2: DNS Qeydlərini Təyin Edin

1. Freenom-da domain-inizi açın
2. **"Manage Domain"** → **"Manage Freenom DNS"** bölməsinə keçin
3. Resend-dən alacağınız DNS qeydlərini əlavə edin (Addım 3-də)

### Addım 3: Resend-də Domain Əlavə Edin

1. **https://resend.com** saytına daxil olun
2. **"Domains"** bölməsinə keçin
3. **"Add Domain"** basın
4. Domain adınızı daxil edin (məsələn: `mail.mezuniyyet.tk`)
5. Resend sizə DNS qeydlərini verəcək:
   - SPF qeydi (TXT)
   - DKIM qeydi (TXT)
   - CNAME qeydi
6. Bu qeydləri Freenom-da əlavə edin (Addım 2)
7. DNS dəyişikliklərinin yayılması 24-48 saat çəkə bilər
8. Resend-də **"Verify Domain"** basın

### Addım 4: Render.com-da Email Ünvanını Yeniləyin

1. Render.com-da servisinizi açın
2. **"Environment"** sekmesinə keçin
3. `RESEND_FROM_EMAIL` variable-ını yeniləyin:
   - **Key:** `RESEND_FROM_EMAIL`
   - **Value:** `noreply@mail.mezuniyyet.tk` (və ya domain-inizə uyğun)
4. **"Save Changes"** basın
5. Servisi yenidən başladın

---

## 💡 Tövsiyə

**Qısa müddət üçün:** Resend-in default domain-i (`onboarding@resend.dev`) istifadə edin - dərhal işləyir və heç bir quraşdırma tələb etmir.

**Uzunmüddətli üçün:** Freenom-dan pulsuz domain əldə edin və Resend-də təsdiqləyin - daha peşəkar görünür və məhdudiyyətsiz email göndərə bilərsiniz.

---

## ⚠️ Freenom Məhdudiyyətləri

- Pulsuz domainlər bəzən etibarsız hesab edilə bilər
- SEO baxımından təsiri zəif ola bilər
- Bəzi email servisləri bu domainləri spam kimi qəbul edə bilər
- Domain-in mülkiyyəti tam olaraq sizə aid olmaya bilər

---

## 🎉 Hazır!

Domain təsdiqləndikdən sonra email göndərmə işləyəcək!

