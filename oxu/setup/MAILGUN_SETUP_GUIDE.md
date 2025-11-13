# 📧 Mailgun Quraşdırması - Addım-Addım Təlimat

## 🎯 Məqsəd
Render.com-da SMTP portları bloklanıb, ona görə Mailgun API istifadə edirik. Mailgun telefon tələb etmir və quraşdırması sadədir.

---

## 📋 Addım 1: Mailgun Hesabı Yaradın

1. **https://www.mailgun.com** saytına gedin
2. **"Sign Up"** düyməsinə basın
3. Email və şifrə ilə qeydiyyatdan keçin
   - Email: `vacationseasonplans@gmail.com` (və ya istədiyiniz email)
   - Şifrə: Güclü şifrə yaradın
   - **Qeyd:** Telefon nömrəsi tələb edilmir! ✅

---

## 📋 Addım 2: Mailgun Dashboard-da Domain Tapın

1. Mailgun hesabınıza daxil olun
2. Sol menyudan **"Sending"** → **"Domains"** bölməsinə keçin
3. **Sandbox Domain** görəcəksiniz (məsələn: `sandbox12345.mailgun.org`)
   - Bu domain avtomatik verilir
   - Format: `sandboxXXXXX.mailgun.org`
4. **Bu domain-i kopyalayın və saxlayın!** 📝

---

## 📋 Addım 3: API Key Alın

1. Mailgun dashboard-da **"Settings"** → **"API Keys"** bölməsinə keçin
2. **"Private API key"** bölməsində API key görəcəksiniz
3. **"Reveal"** və ya **"Show"** basın
4. **API key-i kopyalayın və saxlayın!** 📝
   - Format: `key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 📋 Addım 4: Sender Email Təsdiqləyin (Sandbox üçün)

**Qeyd:** Sandbox domain ilə yalnız təsdiqlənmiş email ünvanlarına göndərə bilərsiniz.

1. Mailgun dashboard-da **"Sending"** → **"Authorized Recipients"** bölməsinə keçin
2. **"Add New"** düyməsinə basın
3. Email ünvanı daxil edin: `vacationseasonplans@gmail.com`
4. **"Add"** basın
5. Email qutunuzu yoxlayın - Mailgun-dan təsdiq emaili gələcək
6. Email-də **"Yes, authorize this recipient"** linkinə basın

**Əlavə:** İstədiyiniz qədər email ünvanı əlavə edə bilərsiniz (test üçün).

---

## 📋 Addım 5: Render.com-da Environment Variable-ları Təyin Edin

1. **https://render.com** saytına gedin və hesabınıza daxil olun
2. Dashboard-da **"mezuniyyet-serverim"** servisinizi tapın və açın
3. Sol menyudan **"Environment"** sekmesinə keçin
4. Aşağıdakı variable-ları əlavə edin:

### Variable 1: USE_MAILGUN
- **Key:** `USE_MAILGUN`
- **Value:** `true`
- **"Save Changes"** basın

### Variable 2: MAILGUN_API_KEY
- **Key:** `MAILGUN_API_KEY`
- **Value:** Addım 3-də aldığınız API key (məsələn: `key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- **"Save Changes"** basın

### Variable 3: MAILGUN_DOMAIN
- **Key:** `MAILGUN_DOMAIN`
- **Value:** Addım 2-də aldığınız Sandbox domain (məsələn: `sandbox12345.mailgun.org`)
- **"Save Changes"** basın

### Variable 4: SENDER_EMAIL (artıq mövcuddur, yoxlayın)
- **Key:** `SENDER_EMAIL`
- **Value:** `vacationseasonplans@gmail.com`
- Bu variable artıq mövcuddur, amma yoxlayın

---

## 📋 Addım 6: Servisi Yenidən Başladın

1. Render.com dashboard-da servisinizdə **"Manual Deploy"** → **"Deploy latest commit"** basın
2. Və ya servis avtomatik yenilənəcək (bir neçə dəqiqə çəkə bilər)

---

## ✅ Test Etmə

1. Proqramı işə salın
2. Şifrə sıfırlama funksiyasını test edin
3. Email göndərməyə cəhd edin
4. Render.com loglarında görünəcək:
   ```
   ✅ [SERVER_API] Email Mailgun ilə uğurla göndərildi
   ```

---

## 🔍 Problem Həlləri

### Problem: "Mailgun konfiqurasiyası yoxdur"
**Həll:** Render.com-da `USE_MAILGUN`, `MAILGUN_API_KEY` və `MAILGUN_DOMAIN` variable-larını yoxlayın

### Problem: "Email göndərilmədi"
**Həll:** 
- Sandbox domain istifadə edirsinizsə, email ünvanını "Authorized Recipients" siyahısına əlavə edin
- API key-in düzgün olduğunu yoxlayın
- Domain-in düzgün olduğunu yoxlayın

### Problem: "401 Unauthorized"
**Həll:** API key səhvdir, yenidən yoxlayın

---

## 📝 Xülasə

**Lazım olan məlumatlar:**
1. ✅ Mailgun hesabı (telefon tələb etmir)
2. ✅ Sandbox Domain (məsələn: `sandbox12345.mailgun.org`)
3. ✅ API Key (məsələn: `key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
4. ✅ Render.com-da 3 environment variable

**Render.com-da təyin ediləcək variable-lar:**
- `USE_MAILGUN` = `true`
- `MAILGUN_API_KEY` = `your-api-key-here`
- `MAILGUN_DOMAIN` = `sandbox12345.mailgun.org`

---

## 🎉 Hazır!

Bütün addımları tamamladıqdan sonra email göndərmə işləyəcək!

