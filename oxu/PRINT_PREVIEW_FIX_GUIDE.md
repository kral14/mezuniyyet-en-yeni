# Çap Önizləmə Probleminin Həlli Təlimatı

## Problem Təsviri

Çap önizləmə pəncərəsində HTML məzmunu düzgün render edilmir, əvəzinə HTML kodunun özü göstərilir. Bu problem HTML məzmununun düzgün render edilməməsindən qaynaqlanır.

## Həll Yolları

### 1. WebView Modulu Quraşdırma

WebView modulu HTML məzmununu düzgün render edir:

```bash
pip install pywebview
```

### 2. wkhtmltopdf Quraşdırma (PDF üçün)

PDF yaratmaq üçün wkhtmltopdf quraşdırın:

1. https://wkhtmltopdf.org/downloads.html saytına gedin
2. Windows üçün installer yükləyin
3. Quraşdırın
4. PATH environment variable-ə əlavə edin

Və ya Chocolatey ilə:
```bash
choco install wkhtmltopdf
```

### 3. Test Faylları

#### Test 1: Əsas Test
```bash
python test_print_preview_fix.py
```

#### Test 2: Təkmilləşdirilmiş Test
```bash
python improved_print_preview.py
```

#### Test 3: Fix Test
```bash
python fix_print_preview.py
```

### 4. Əsas Proqramda Dəyişikliklər

#### A. Yeni Print Preview Modulu

`src/ui/print_preview_window.py` faylını əlavə edin:

```python
from src.ui.print_preview_window import PrintPreviewWindow, create_vacation_report_html

# İstifadə nümunəsi:
html_content = create_vacation_report_html(
    employee_name="Nəsibbəy Kələşov",
    position="Proqramçı", 
    department="İT Departamenti"
)

PrintPreviewWindow(parent_window, html_content, "Məzuniyyət Tarixçəsi")
```

#### B. Requirements Faylına Əlavə

`src/config/requirements.txt` faylına əlavə edin:

```
pywebview==4.4.1
beautifulsoup4==4.12.2
lxml==4.9.3
reportlab==4.0.7
Pillow==10.1.0
```

### 5. Alternativ Həllər

#### A. Browser-də Açmaq

WebView yoxdursa, HTML-i browser-də açır:

```python
import webbrowser
import tempfile

# HTML-i temp fayla yaz
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
    f.write(html_content)
    temp_file = f.name

# Browser-də aç
webbrowser.open(f'file://{temp_file}')
```

#### B. Selenium istifadə etmək

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

driver.get(f'file://{temp_file}')
# Screenshot çək və ya PDF yarat
```

### 6. Təkmilləşdirilmiş Xüsusiyyətlər

#### A. Tab Sistemi
- Önizləmə tab-ı
- HTML kodu tab-ı

#### B. Toolbar Funksiyaları
- Çap et
- PDF-ə çevir
- HTML-ə yaddaş et
- Browser-də aç
- Zoom kontrolları

#### C. Status Bar
- Real-time status məlumatları
- Xəta mesajları

### 7. Debug və Test

#### A. Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### B. Error Handling
```python
try:
    import webview
    # WebView istifadə et
except ImportError:
    # Browser-də aç
except Exception as e:
    # Xəta mesajı göstər
```

### 8. Performans Optimizasiyası

#### A. Lazy Loading
HTML məzmununu yalnız lazım olduqda yüklə

#### B. Caching
Temp faylları cache et

#### C. Threading
WebView-i ayrı thread-də işə sal

### 9. Test Nümunələri

#### A. Sadə HTML Test
```python
html_content = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Test Səhifəsi</h1></body>
</html>
"""
```

#### B. Məzuniyyət Hesabatı Test
```python
html_content = create_vacation_report_html(
    employee_name="Test İşçi",
    position="Test Vəzifə",
    department="Test Departament"
)
```

### 10. Deployment

#### A. EXE Build
PyInstaller ilə build edərkən WebView modulunu daxil et:

```python
# build_exe.py
hidden_imports = ['webview']
```

#### B. Requirements
Bütün tələb olunan modulları requirements.txt-ə əlavə et

## Nəticə

Bu təlimatı izlədikdən sonra çap önizləmə funksiyası düzgün işləyəcək və HTML məzmunu render ediləcək.

### Əsas Fayllar:
- `test_print_preview_fix.py` - Əsas test
- `improved_print_preview.py` - Təkmilləşdirilmiş test  
- `fix_print_preview.py` - Fix test
- `src/ui/print_preview_window.py` - Əsas modul
- `print_preview_requirements.txt` - Tələb olunan modullar

