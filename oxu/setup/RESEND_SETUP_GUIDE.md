# 📧 Resend Quraşdırması - Addım-Addım Təlimat

## 🎯 Məqsəd
Render.com-da SMTP portları bloklanıb, ona görə Resend API istifadə edirik. Resend **pulsuz plan** təklif edir və **telefon tələb etmir**! ✅

---

## 📋 Addım 1: Resend Hesabı Yaradın

1. **https://resend.com** saytına gedin
2. **"Sign Up"** və ya **"Get Started"** düyməsinə basın
3. Email və şifrə ilə qeydiyyatdan keçin
   - Email: `vacationseasonplans@gmail.com` (və ya istədiyiniz email)
   - Şifrə: Güclü şifrə yaradın
   - **Qeyd:** Telefon nömrəsi və ödəniş kartı tələb edilmir! ✅

---

## 📋 Addım 2: API Key Alın

1. Resend hesabınıza daxil olun
2. Dashboard-da **"API Keys"** bölməsinə keçin
3. **"Create API Key"** düyməsinə basın
4. API key adı verin (məsələn: "Render Server")
5. **"Add"** və ya **"Create"** basın
6. **API key-i kopyalayın və saxlayın!** 📝
   - Format: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Qeyd:** API key yalnız bir dəfə göstərilir, ona görə dərhal kopyalayın!

---

## 📋 Addım 3: Domain Əlavə Edin (İstəyə görə)

**Qeyd:** Resend pulsuz plan ilə də işləyir, amma öz domain-inizi əlavə etsəniz daha yaxşıdır.

1. Resend dashboard-da **"Domains"** bölməsinə keçin
2. **"Add Domain"** basın
3. Domain adınızı daxil edin (məsələn: `mail.sizin-domain.com`)
4. DNS qeydlərini əlavə edin (SPF, DKIM, və s.)
5. Domain təsdiqlənəndən sonra istifadə edə bilərsiniz

**Alternativ:** Domain əlavə etməsəniz də, Resend öz domain-i ilə email göndərə bilər.

---

## 📋 Addım 4: Render.com-da Environment Variable Təyin Edin

1. **https://render.com** saytına gedin və hesabınıza daxil olun
2. Dashboard-da **"mezuniyyet-serverim"** servisinizi tapın və açın
3. Sol menyudan **"Environment"** sekmesinə keçin
4. Aşağıdakı variable-ı əlavə edin:

### Variable: USE_RESEND
- **Key:** `USE_RESEND`
- **Value:** `true`
- **"Save Changes"** basın

### Variable: RESEND_API_KEY
- **Key:** `RESEND_API_KEY`
- **Value:** Addım 2-də aldığınız API key (məsələn: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
- **"Save Changes"** basın

### Variable: SENDER_EMAIL (artıq mövcuddur, yoxlayın)
- **Key:** `SENDER_EMAIL`
- **Value:** `vacationseasonplans@gmail.com`
- Bu variable artıq mövcuddur, amma yoxlayın

---

## 📋 Addım 5: Servisi Yenidən Başladın

1. Render.com dashboard-da servisinizdə **"Manual Deploy"** → **"Deploy latest commit"** basın
2. Və ya servis avtomatik yenilənəcək (bir neçə dəqiqə çəkə bilər)

---

## ✅ Test Etmə

1. Proqramı işə salın
2. Şifrə sıfırlama funksiyasını test edin
3. Email göndərməyə cəhd edin
4. Render.com loglarında görünəcək:
   ```
   ✅ [SERVER_API] Email Resend ilə uğurla göndərildi
   ```

---

## 🔍 Problem Həlləri

### Problem: "Resend API key yoxdur"
**Həll:** Render.com-da `USE_RESEND` və `RESEND_API_KEY` variable-larını yoxlayın

### Problem: "Email göndərilmədi"
**Həll:** 
- API key-in düzgün olduğunu yoxlayın
- Resend dashboard-da API key-in aktiv olduğunu yoxlayın
- Render.com loglarında xəta mesajını yoxlayın

### Problem: "401 Unauthorized"
**Həll:** API key səhvdir, yenidən yoxlayın və Resend dashboard-da yeni API key yaradın

---

## 💰 Resend Pulsuz Plan

- **100 email/gün** pulsuz
- **3,000 email/ay** pulsuz
- Telefon tələb etmir
- Ödəniş kartı tələb etmir
- API key dərhal işləyir

---

## 📝 Xülasə

**Lazım olan məlumatlar:**
1. ✅ Resend hesabı (telefon və ödəniş kartı tələb etmir)
2. ✅ API Key (məsələn: `re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Render.com-da təyin ediləcək variable-lar:**
- `USE_RESEND` = `true`
- `RESEND_API_KEY` = `your-api-key-here`

---

## 🎉 Hazır!

Bütün addımları tamamladıqdan sonra email göndərmə işləyəcək!

**Resend-in üstünlükləri:**
- ✅ Pulsuz plan (100 email/gün)
- ✅ Telefon tələb etmir
- ✅ Ödəniş kartı tələb etmir
- ✅ Quraşdırması çox sadədir
- ✅ API key dərhal işləyir

