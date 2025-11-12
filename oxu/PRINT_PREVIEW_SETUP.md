# Çap Önizləmə və PDF Çevirmə Quraşdırması

Bu sənəd çap önizləmə və PDF çevirmə funksionallığının quraşdırılması üçün təlimatları ehtiva edir.

## Yeni Funksionallıq

### ✨ Əlavə edilən xüsusiyyətlər:

1. **Çap Önizləmə Pəncərəsi** - Çap ediləcək sənədlərin önizləməsini göstərir
2. **PDF Çevirmə** - HTML sənədlərini PDF formatına çevirir
3. **Zoom Kontrolları** - Önizləmədə zoom in/out funksionallığı
4. **Fayl Yaddaş** - PDF və HTML fayllarını yaddaş etmə imkanı

### 🎯 İstifadə yolları:

1. **İşçi məlumatları pəncərəsində:**
   - "👁️ Bütün Məzuniyyətləri Önizləmə ilə Çap Et" düyməsi
   - "👁️ Seçilmiş Məzuniyyəti Önizləmə ilə Çap Et" düyməsi

2. **Məzuniyyət formunda:**
   - "👁️ Önizləmə" düyməsi (çap düyməsinin yanında)

## Quraşdırma

### 1. PDF Kitabxanalarını Quraşdırın

```bash
# WeasyPrint (tövsiyə edilir)
pip install weasyprint

# Və ya ReportLab (alternativ)
pip install reportlab

# Əlavə tələblər
pip install cffi cairocffi Pillow beautifulsoup4 lxml
```

### 2. Avtomatik Quraşdırma

```bash
# requirements_print.txt faylını istifadə edin
pip install -r src/requirements_print.txt
```

## İstifadə

### Çap Önizləmə Pəncərəsi

1. İstənilən çap düyməsini basın
2. Önizləmə pəncərəsi açılacaq
3. Pəncərədə aşağıdakı funksionallıq mövcuddur:
   - **🖨️ Çap Et** - Brauzer-də açır və çap edir
   - **📄 PDF-ə Çevir** - PDF faylı yaradır
   - **💾 HTML-ə Yaddaş** - HTML faylı yaddaş edir
   - **➕/➖ Zoom** - Önizləməni böyüdür/kiçildir
   - **❌ Bağla** - Pəncərəni bağlayır

### PDF Çevirmə

1. Önizləmə pəncərəsində "📄 PDF-ə Çevir" düyməsini basın
2. Fayl yaddaş dialoqu açılacaq
3. PDF faylının yerini seçin və "Yaddaş Et" basın
4. PDF faylı yaradılacaq

## Texniki Detallar

### Dəstəklənən Kitabxanalar

- **WeasyPrint** (tövsiyə edilir) - HTML-dən PDF-ə yüksək keyfiyyətli çevirmə
- **ReportLab** (alternativ) - Python-da PDF yaradıcısı

### Fayl Strukturu

```
src/
├── ui/
│   └── print_preview_window.py    # Önizləmə pəncərəsi
├── utils/
│   └── print_service.py           # PDF çevirmə funksiyaları
└── requirements_print.txt         # PDF kitabxanaları
```

## Xəta Həlləri

### WeasyPrint Quraşdırma Xətası

```bash
# Windows üçün
pip install --upgrade pip
pip install weasyprint

# Linux üçün
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
pip install weasyprint
```

### ReportLab Alternativi

Əgər WeasyPrint quraşdırıla bilmirsə, ReportLab avtomatik olaraq istifadə ediləcək:

```bash
pip install reportlab
```

## Qeydlər

- PDF çevirmə funksionallığı tam HTML CSS dəstəyi ilə işləyir
- Önizləmə pəncərəsi real HTML rendering göstərir
- Bütün çap funksiyaları mövcud formatları saxlayır
- PDF faylları A4 formatında yaradılır
