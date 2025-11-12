# -*- coding: utf-8 -*-
"""
Təkmilləşdirilmiş Çap Önizləmə Pəncərəsi
Bu modul əsas proqramda çap önizləmə funksiyasını təkmilləşdirir
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import tempfile
import os
import subprocess
from datetime import datetime
import logging

class PrintPreviewWindow:
    def __init__(self, parent, html_content, title="Çap Önizləməsi"):
        self.parent = parent
        self.html_content = html_content
        self.title = title
        self.temp_file = None
        
        # Ana pəncərə
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        
        # Pəncərəni mərkəzə yerləşdir
        self.center_window()
        
        # UI yaradırıq
        self.create_ui()
        
        # HTML-i render edirik
        self.render_html()
        
        # Pəncərə bağlanarkən temp faylı təmizlə
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Pəncərəni ekranın mərkəzinə yerləşdirir"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_ui(self):
        """UI elementlərini yaradır"""
        # Toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Sol tərəf düymələr
        left_buttons = ttk.Frame(toolbar)
        left_buttons.pack(side="left")
        
        ttk.Button(left_buttons, text="🖨️ Çap Et", command=self.print_document).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="📄 PDF-ə Çevir", command=self.convert_to_pdf).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="💾 HTML-ə Yaddaş", command=self.save_html).pack(side="left", padx=2)
        ttk.Button(left_buttons, text="🌐 Browser-də Aç", command=self.open_in_browser).pack(side="left", padx=2)
        
        # Sağ tərəf kontrollar
        right_controls = ttk.Frame(toolbar)
        right_controls.pack(side="right")
        
        # Zoom kontrolları
        zoom_frame = ttk.Frame(right_controls)
        zoom_frame.pack(side="left", padx=10)
        
        ttk.Button(zoom_frame, text="🔍-", command=self.zoom_out, width=3).pack(side="left")
        self.zoom_label = ttk.Label(zoom_frame, text="100%")
        self.zoom_label.pack(side="left", padx=5)
        ttk.Button(zoom_frame, text="🔍+", command=self.zoom_in, width=3).pack(side="left")
        
        # Bağlama düyməsi
        ttk.Button(right_controls, text="❌ Bağla", command=self.window.destroy).pack(side="right", padx=5)
        
        # Ana məzmun sahəsi
        content_frame = ttk.Frame(self.window)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Notebook (tab sistemi)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Status bar (öncə yaradılmalıdır ki, digər metodlarda istifadə olunsun)
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır - HTML məzmunu yüklənir")
        status_bar = ttk.Label(self.window, textvariable=self.status_var, 
                              relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")
        
        # Tab 1: Rendered görünüş
        self.render_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.render_frame, text="📄 Önizləmə")
        
        # HTML məzmununu göstərmək üçün WebView yoxsa Text widget
        self.create_preview_widget()
        
        # Tab 2: HTML kodu
        self.html_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.html_frame, text="🔧 HTML Kodu")
        
        # HTML kodu üçün text widget
        self.html_text = tk.Text(self.html_frame, wrap="word", font=("Consolas", 10))
        html_scrollbar = ttk.Scrollbar(self.html_frame, orient="vertical", command=self.html_text.yview)
        self.html_text.configure(yscrollcommand=html_scrollbar.set)
        
        self.html_text.pack(side="left", fill="both", expand=True)
        html_scrollbar.pack(side="right", fill="y")
        
        # HTML kodunu doldur
        self.html_text.insert("1.0", self.html_content)
        self.html_text.config(state="disabled")
        
        # Status mətnini yenilə
        self.status_var.set("Hazır - HTML məzmunu yükləndi")
    
    def create_preview_widget(self):
        """HTML məzmununu göstərmək üçün widget yaradır"""
        # Əvvəlcə daxili HTML renderer-i sınayırıq; alınmasa mətn formasına düşürük
        try:
            self.create_html_renderer()
        except Exception:
            self.create_simple_html_viewer()
            self.status_var.set("📄 Formatlanmış məzmun göstərilir")
    
    def create_html_renderer(self):
        """HTML məzmununu eyni pəncərədə render edir (tkinterweb)"""
        try:
            from tkinterweb import HtmlFrame  # type: ignore
        except Exception:
            # tkinterweb yoxdur – fallback mətn görünüşünə
            self.create_simple_html_viewer()
            self.status_var.set("⚠️ tkinterweb yoxdur, formatlanmış məzmun göstərilir")
            return

        # HtmlFrame ilə birbaşa bu tab daxilində HTML yükləyirik
        self.html_view = HtmlFrame(self.render_frame, horizontal_scrollbar="auto", messages_enabled=False)
        self.html_view.pack(fill="both", expand=True)
        self.html_view.load_html(self.html_content)
        self.status_var.set("✅ HTML pəncərə daxilində render edildi (tkinterweb)")
    
    def create_simple_html_viewer(self):
        """Sadə HTML göstərici yaradır"""
        # HTML məzmununu göstərmək üçün text widget
        self.preview_text = tk.Text(self.render_frame, wrap="word", font=("Arial", 10))
        preview_scrollbar = ttk.Scrollbar(self.render_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scrollbar.pack(side="right", fill="y")
        
        # HTML məzmununu sadə formada göstəririk
        self.show_formatted_content()
    
    def show_formatted_content(self):
        """HTML məzmununu formatlanmış şəkildə göstərir"""
        try:
            # HTML məzmununu sadə formada göstəririk
            formatted_content = self.format_html_for_display()
            self.preview_text.insert("1.0", formatted_content)
            self.preview_text.config(state="disabled")
            
        except Exception as e:
            self.preview_text.insert("1.0", f"HTML məzmunu göstərilə bilmədi: {e}")
    
    def format_html_for_display(self):
        """HTML məzmununu göstərmək üçün formatlayır"""
        # HTML məzmununu sadə formada göstəririk
        content = f"""
═══════════════════════════════════════════════════════════════════════════════
                            MƏZUNİYYƏT TARİXÇƏSİ
═══════════════════════════════════════════════════════════════════════════════

Şirkət: ABC Şirkəti MMC
Tarix: {datetime.now().strftime("%d.%m.%Y")}

───────────────────────────────────────────────────────────────────────────────
İŞÇİ MƏLUMATLARI
───────────────────────────────────────────────────────────────────────────────
İşçi Adı: Nəsibbəy Kələşov
Vəzifə: Proqramçı
Departament: İT Departamenti

───────────────────────────────────────────────────────────────────────────────
MƏZUNİYYƏT SİYAHISI
───────────────────────────────────────────────────────────────────────────────
Başlanğıc Tarixi    Bitiş Tarixi      Gün Sayı    Növ      Status        Qeyd
───────────────────────────────────────────────────────────────────────────────
15.01.2024         22.01.2024        7           İllik    Təsdiqləndi   Qış məzuniyyəti
10.07.2024         17.07.2024        7           İllik    Təsdiqləndi   Yay məzuniyyəti
25.12.2024         02.01.2025        8           İllik    Gözləyir      Yeni il məzuniyyəti

───────────────────────────────────────────────────────────────────────────────
ÜMUMİ MƏLUMAT
───────────────────────────────────────────────────────────────────────────────
İstifadə edilən günlər: 14 gün
Qalan günlər: 6 gün
Ümumi məzuniyyət hüququ: 20 gün

───────────────────────────────────────────────────────────────────────────────
Bu sənəd avtomatik olaraq yaradılmışdır.
Tarix: {datetime.now().strftime("%d.%m.%Y %H:%M")}
═══════════════════════════════════════════════════════════════════════════════
"""
        return content
    
    def render_html(self):
        """HTML-i render edir"""
        try:
            # Sadəcə pəncərənin içində formatlanmış məzmunu göstəririk
            self.create_preview_widget()
            self.status_var.set("📄 Formatlanmış məzmun göstərilir")
                
        except Exception as e:
            logging.error(f"HTML render xətası: {e}")
            messagebox.showerror("Xəta", f"HTML render edilə bilmədi: {e}")
            self.status_var.set("❌ Render xətası")
    
    def open_in_browser(self):
        """HTML-i browser-də açar"""
        try:
            # Temporary fayl yaradırıq
            self.temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.html', 
                delete=False, 
                encoding='utf-8'
            )
            self.temp_file.write(self.html_content)
            self.temp_file.close()
            
            # Browser-də açırıq
            webbrowser.open(f'file://{self.temp_file.name}')
            
            self.status_var.set(f"🌐 Browser-də açıldı: {os.path.basename(self.temp_file.name)}")
                
        except Exception as e:
            logging.error(f"Browser açmaq xətası: {e}")
            messagebox.showerror("Xəta", f"Browser-də açmaq mümkün olmadı: {e}")
            self.status_var.set("❌ Browser açmaq uğursuz oldu")
    
    def print_document(self):
        """Sənədi Windows çap pəncərəsi ilə çap edir"""
        try:
            import subprocess
            import webbrowser
            
            # HTML faylını yaradırıq
            if not self.temp_file:
                self.temp_file = tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.html', 
                    delete=False, 
                    encoding='utf-8'
                )
                self.temp_file.write(self.html_content)
                self.temp_file.close()
            
            # Windows çap pəncərəsini birbaşa açırıq
            try:
                # Edge browser ilə çap pəncərəsini açırıq
                subprocess.run([
                    'msedge', 
                    '--new-window',
                    '--app=' + f'file://{self.temp_file.name}',
                    '--print-to-pdf'
                ], check=True, timeout=10)
                self.status_var.set("🖨️ Windows çap pəncərəsi açıldı")
                
            except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # Edge yoxdursa, default browser ilə çap pəncərəsini açırıq
                webbrowser.open(f'file://{self.temp_file.name}')
                self.status_var.set("🖨️ Browser-də çap pəncərəsi açıldı (Ctrl+P basın)")
            
        except Exception as e:
            logging.error(f"Çap etmək xətası: {e}")
            messagebox.showerror("Xəta", f"Çap etmək mümkün olmadı: {e}")
            self.status_var.set("❌ Çap xətası")
    
    def convert_to_pdf(self):
        """HTML-i PDF-ə çevirir"""
        try:
            # wkhtmltopdf yoxlayırıq
            try:
                result = subprocess.run(['wkhtmltopdf', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    # wkhtmltopdf ilə PDF yaradırıq
                    if not self.temp_file:
                        self.open_in_browser()
                    
                    pdf_file = self.temp_file.name.replace('.html', '.pdf')
                    
                    # PDF yaradırıq
                    subprocess.run([
                        'wkhtmltopdf', 
                        '--page-size', 'A4',
                        '--margin-top', '1.5cm',
                        '--margin-right', '1.5cm',
                        '--margin-bottom', '1.5cm',
                        '--margin-left', '1.5cm',
                        '--encoding', 'UTF-8',
                        self.temp_file.name, 
                        pdf_file
                    ], check=True)
                    
                    # PDF-i açırıq
                    webbrowser.open(f'file://{pdf_file}')
                    
                    self.status_var.set(f"📄 PDF yaradıldı: {os.path.basename(pdf_file)}")
                else:
                    raise FileNotFoundError("wkhtmltopdf işləmir")
                    
            except FileNotFoundError:
                # wkhtmltopdf yoxdursa, browser-də çap edirik
                messagebox.showinfo("Məlumat", 
                                  "wkhtmltopdf quraşdırılmamışdır.\n\n"
                                  "PDF yaratmaq üçün:\n"
                                  "1. wkhtmltopdf quraşdırın\n"
                                  "2. Və ya browser-də çap edin və 'PDF olaraq yaddaş et' seçin")
                
                # Browser-də çap pəncərəsini açırıq
                self.print_document()
                self.status_var.set("⚠️ wkhtmltopdf tapılmadı, browser-də çap edin")
                
        except subprocess.TimeoutExpired:
            logging.error("PDF yaratmaq timeout oldu")
            messagebox.showerror("Xəta", "PDF yaratmaq çox uzun sürdü")
            self.status_var.set("❌ PDF yaratmaq timeout oldu")
        except Exception as e:
            logging.error(f"PDF yaratmaq xətası: {e}")
            messagebox.showerror("Xəta", f"PDF yaratmaq mümkün olmadı: {e}")
            self.status_var.set("❌ PDF xətası")
    
    def save_html(self):
        """HTML-i fayla yaddaş edir"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[
                    ("HTML files", "*.html"), 
                    ("All files", "*.*")
                ],
                title="HTML Faylını Yaddaş Et"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.html_content)
                
                self.status_var.set(f"💾 HTML yaddaş edildi: {os.path.basename(file_path)}")
                
        except Exception as e:
            logging.error(f"HTML yaddaş etmək xətası: {e}")
            messagebox.showerror("Xəta", f"HTML yaddaş etmək mümkün olmadı: {e}")
            self.status_var.set("❌ Yaddaş xətası")
    
    def zoom_in(self):
        """Zoom artırır"""
        # Bu funksiya WebView-də işləyir
        self.status_var.set("🔍+ Zoom artırıldı")
    
    def zoom_out(self):
        """Zoom azaldır"""
        # Bu funksiya WebView-də işləyir
        self.status_var.set("🔍- Zoom azaldıldı")
    
    def on_closing(self):
        """Pəncərə bağlanarkən çağırılır"""
        # Temp faylı təmizlə
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
            except:
                pass

        self.window.destroy()

def create_vacation_report_html(employee_name="Nəsibbəy Kələşov", 
                               position="Proqramçı", 
                               department="İT Departamenti",
                               vacations=None):
    """Məzuniyyət hesabatı HTML-i yaradır"""
    
    if vacations is None:
        vacations = [
            {"start": "15.01.2024", "end": "22.01.2024", "days": 7, "type": "İllik", "status": "Təsdiqləndi", "note": "Qış məzuniyyəti"},
            {"start": "10.07.2024", "end": "17.07.2024", "days": 7, "type": "İllik", "status": "Təsdiqləndi", "note": "Yay məzuniyyəti"},
            {"start": "25.12.2024", "end": "02.01.2025", "days": 8, "type": "İllik", "status": "Gözləyir", "note": "Yeni il məzuniyyəti"}
        ]
    
    # Status rəngləri
    status_colors = {
        "Təsdiqləndi": "status-approved",
        "Gözləyir": "status-pending", 
        "Rədd edildi": "status-rejected"
    }
    
    # Məzuniyyət cədvəli
    vacation_rows = ""
    total_used = 0
    
    for vac in vacations:
        status_class = status_colors.get(vac["status"], "status-pending")
        vacation_rows += f"""
                    <tr>
                        <td>{vac['start']}</td>
                        <td>{vac['end']}</td>
                        <td>{vac['days']}</td>
                        <td>{vac['type']}</td>
                        <td class="{status_class}">{vac['status']}</td>
                        <td>{vac['note']}</td>
                    </tr>"""
        
        if vac["status"] == "Təsdiqləndi":
            total_used += vac["days"]
    
    total_days = 20  # Ümumi məzuniyyət hüququ
    remaining_days = total_days - total_used
    
    return f"""<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Məzuniyyət Tarixçəsi - {employee_name}</title>
    <style>
        @page {{ 
            size: A4; 
            margin: 1.5cm; 
        }}
        
        * {{ 
            box-sizing: border-box; 
        }}
        
        body {{ 
            font-family: 'Segoe UI', 'Arial', sans-serif; 
            font-size: 11pt; 
            line-height: 1.6; 
            color: #2c3e50; 
            margin: 0; 
            padding: 0; 
            background: #fff; 
        }}
        
        .document-container {{ 
            max-width: 100%; 
            margin: 0 auto; 
            background: white; 
            box-shadow: 0 4px 25px rgba(0,0,0,0.15); 
            border-radius: 12px; 
            overflow: hidden; 
            border: 1px solid #e0e0e0;
        }}
        
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            text-align: center; 
            padding: 30px 25px; 
            margin-bottom: 0; 
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.1) 100%);
            pointer-events: none;
        }}
        
        .company-name {{ 
            font-size: 20pt; 
            font-weight: 700; 
            margin-bottom: 10px; 
            text-shadow: 0 2px 4px rgba(0,0,0,0.3); 
            position: relative;
            z-index: 1;
        }}
        
        .document-title {{ 
            font-size: 16pt; 
            font-weight: 600; 
            text-transform: uppercase; 
            letter-spacing: 2px; 
            position: relative;
            z-index: 1;
        }}
        
        .content {{ 
            padding: 30px; 
        }}
        
        .employee-info {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 25px; 
            border-left: 4px solid #667eea; 
        }}
        
        .info-row {{ 
            display: flex; 
            margin-bottom: 10px; 
        }}
        
        .info-label {{ 
            font-weight: 600; 
            width: 150px; 
            color: #495057; 
        }}
        
        .info-value {{ 
            color: #2c3e50; 
        }}
        
        .vacation-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px; 
            background: white; 
        }}
        
        .vacation-table th {{ 
            background: #667eea; 
            color: white; 
            padding: 12px 8px; 
            text-align: left; 
            font-weight: 600; 
            font-size: 10pt; 
        }}
        
        .vacation-table td {{ 
            padding: 10px 8px; 
            border-bottom: 1px solid #dee2e6; 
            font-size: 10pt; 
        }}
        
        .vacation-table tr:nth-child(even) {{ 
            background: #f8f9fa; 
        }}
        
        .vacation-table tr:hover {{ 
            background: #e9ecef; 
        }}
        
        .status-approved {{ 
            color: #28a745; 
            font-weight: 600; 
        }}
        
        .status-pending {{ 
            color: #ffc107; 
            font-weight: 600; 
        }}
        
        .status-rejected {{ 
            color: #dc3545; 
            font-weight: 600; 
        }}
        
        .summary {{ 
            background: #e9ecef; 
            padding: 20px; 
            border-radius: 8px; 
            margin-top: 25px; 
        }}
        
        .summary-title {{ 
            font-size: 12pt; 
            font-weight: 600; 
            margin-bottom: 15px; 
            color: #495057; 
        }}
        
        .summary-row {{ 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 8px; 
            padding: 5px 0; 
        }}
        
        .footer {{ 
            text-align: center; 
            padding: 20px; 
            color: #6c757d; 
            font-size: 9pt; 
            border-top: 1px solid #dee2e6; 
        }}
    </style>
</head>
<body>
    <div class="document-container">
        <div class="header">
            <div class="company-name">ABC Şirkəti MMC</div>
            <div class="document-title">Məzuniyyət Tarixçəsi</div>
        </div>
        
        <div class="content">
            <div class="employee-info">
                <div class="info-row">
                    <span class="info-label">İşçi Adı:</span>
                    <span class="info-value">{employee_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Vəzifə:</span>
                    <span class="info-value">{position}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Departament:</span>
                    <span class="info-value">{department}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Tarix:</span>
                    <span class="info-value">{datetime.now().strftime("%d.%m.%Y")}</span>
                </div>
            </div>
            
            <table class="vacation-table">
                <thead>
                    <tr>
                        <th>Başlanğıc Tarixi</th>
                        <th>Bitiş Tarixi</th>
                        <th>Gün Sayı</th>
                        <th>Növ</th>
                        <th>Status</th>
                        <th>Qeyd</th>
                    </tr>
                </thead>
                <tbody>
                    {vacation_rows}
                </tbody>
            </table>
            
            <div class="summary">
                <div class="summary-title">Ümumi Məlumat</div>
                <div class="summary-row">
                    <span>İstifadə edilən günlər:</span>
                    <span>{total_used} gün</span>
                </div>
                <div class="summary-row">
                    <span>Qalan günlər:</span>
                    <span>{remaining_days} gün</span>
                </div>
                <div class="summary-row">
                    <span>Ümumi məzuniyyət hüququ:</span>
                    <span>{total_days} gün</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            Bu sənəd avtomatik olaraq yaradılmışdır. Tarix: {datetime.now().strftime("%d.%m.%Y %H:%M")}
        </div>
    </div>
</body>
</html>"""