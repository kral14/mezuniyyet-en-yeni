"""
Məzuniyyət çapı xidməti
Bu modul məzuniyyət məlumatlarını HTML formatında hazırlayır və çap edir
"""

import os
import tempfile
import webbrowser
from datetime import datetime
from typing import Dict, Any, Optional
import csv
import json
import tkinter as tk
from tkinter import filedialog, messagebox

# PDF conversion libraries
# WeasyPrint deaktiv edildi - Windows-də libgobject problemi var
WEASYPRINT_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def calculate_vacation_days_used(vacations):
    """
    Məzuniyyətlərdən istifadə edilmiş günləri hesablayır
    
    Args:
        vacations: Məzuniyyət siyahısı
        
    Returns:
        int: İstifadə edilmiş günlər
    """
    used_days = 0
    
    for vacation in vacations:
        if isinstance(vacation, dict):
            # Tarixlərdən müddəti hesabla
            start_date = vacation.get('baslama', vacation.get('baslangic', ''))
            end_date = vacation.get('bitme', '')
            
            if start_date and end_date:
                try:
                    # datetime.date object-i handle et
                    if hasattr(start_date, 'strftime'):
                        start_str = start_date.strftime('%Y-%m-%d')
                    else:
                        start_str = str(start_date)
                    
                    if hasattr(end_date, 'strftime'):
                        end_str = end_date.strftime('%Y-%m-%d')
                    else:
                        end_str = str(end_date)
                    
                    start_dt = datetime.strptime(start_str, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_str, '%Y-%m-%d')
                    days = (end_dt - start_dt).days + 1
                    used_days += days
                    
                    print(f"DEBUG: Məzuniyyət {start_str} - {end_str}: {days} gün")
                    
                except Exception as e:
                    print(f"DEBUG: Tarix hesablama xətası: {e}")
                    # Fallback: muddet sahəsindən al
                    muddet = vacation.get('muddet', 0)
                    if isinstance(muddet, str):
                        try:
                            muddet = int(muddet.replace(' gün', ''))
                        except:
                            muddet = 0
                    used_days += muddet
            else:
                # Tarixlər yoxdursa, muddet sahəsindən al
                muddet = vacation.get('muddet', 0)
                if isinstance(muddet, str):
                    try:
                        muddet = int(muddet.replace(' gün', ''))
                    except:
                        muddet = 0
                used_days += muddet
    
    print(f"DEBUG: Ümumi istifadə edilmiş günlər: {used_days}")
    return used_days

def generate_vacation_html(employee_data: Dict[str, Any], vacation_data: Dict[str, Any], 
                          company_name: str = "ŞİRKƏT ADI") -> str:
    """
    İşçi və məzuniyyət məlumatlarına əsasən HTML çap formatı yaradır
    
    Args:
        employee_data: İşçi məlumatları
        vacation_data: Məzuniyyət məlumatları  
        company_name: Şirkət adı
        
    Returns:
        HTML string
    """
    
    # Məzuniyyət günlərini hesabla
    total_vacation_days = employee_data.get('umumi_gun', 30)
    vacations = employee_data.get('goturulen_icazeler', [])
    
    print(f"DEBUG: İşçi: {employee_data.get('name')}")
    print(f"DEBUG: Ümumi günlər: {total_vacation_days}")
    print(f"DEBUG: Məzuniyyətlər sayı: {len(vacations)}")
    
    # İstifadə edilmiş günləri düzgün hesabla
    used_days = calculate_vacation_days_used(vacations)
    remaining_days = total_vacation_days - used_days
    
    # Tarixləri format et
    start_date = vacation_data.get('start_date', '')
    end_date = vacation_data.get('end_date', '')
    note = vacation_data.get('note', '')
    
    # Müddəti hesabla
    if start_date and end_date:
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration = (end_dt - start_dt).days + 1
            
            # Tarixləri Azərbaycan formatına çevir
            start_date_formatted = start_dt.strftime('%d.%m.%Y')
            end_date_formatted = end_dt.strftime('%d.%m.%Y')
        except:
            duration = 0
            start_date_formatted = start_date
            end_date_formatted = end_date
    else:
        duration = 0
        start_date_formatted = start_date
        end_date_formatted = end_date
    
    # Bugünkü tarixi format et
    today = datetime.now().strftime('%d.%m.%Y')
    
    html_template = f"""<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Məzuniyyət Vərəqəsi - {employee_data.get('name', 'İşçi')}</title>
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
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 25px 20px;
            margin-bottom: 0;
        }}
        
        .company-name {{
            font-size: 18pt;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .document-title {{
            font-size: 14pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            opacity: 0.95;
        }}
        
        .content-wrapper {{
            padding: 30px;
        }}
        
        .info-section {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 12px;
            border-left: 3px solid #667eea;
        }}
        
        .section-title {{
            font-size: 10pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .section-title::before {{
            content: "👤";
            margin-right: 5px;
            font-size: 10pt;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .info-label {{
            font-weight: 600;
            color: #495057;
            font-size: 8pt;
            margin-bottom: 2px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .info-value {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 2px;
            padding: 5px 8px;
            font-weight: 500;
            color: #2c3e50;
            min-height: 25px;
            display: flex;
            align-items: center;
            font-size: 9pt;
        }}
        
        .vacation-summary {{
            background: #e8f4f8;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 12px;
            border-left: 3px solid #17a2b8;
        }}
        
        .summary-title {{
            font-size: 10pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .summary-title::before {{
            content: "📊";
            margin-right: 5px;
            font-size: 10pt;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }}
        
        .summary-card {{
            background: white;
            border-radius: 3px;
            padding: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .summary-number {{
            font-size: 14pt;
            font-weight: 700;
            color: #667eea;
            display: block;
            margin-bottom: 2px;
        }}
        
        .summary-label {{
            font-size: 7pt;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .vacation-details {{
            background: #fff3cd;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 12px;
            border-left: 3px solid #ffc107;
        }}
        
        .vacation-title {{
            font-size: 10pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .vacation-title::before {{
            content: "📅";
            margin-right: 5px;
            font-size: 10pt;
        }}
        
        .date-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            margin-bottom: 10px;
        }}
        
        .date-card {{
            background: white;
            border-radius: 3px;
            padding: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .date-label {{
            font-size: 7pt;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 3px;
        }}
        
        .date-value {{
            font-size: 9pt;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .note-section {{
            margin-top: 10px;
        }}
        
        .note-label {{
            font-weight: 600;
            color: #495057;
            font-size: 8pt;
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .note-content {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 3px;
            padding: 8px;
            min-height: 40px;
            font-style: italic;
            color: #495057;
            font-size: 8pt;
        }}
        
        .signatures-section {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 12px;
            margin-top: 15px;
        }}
        
        .signatures-title {{
            font-size: 10pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        
        .signatures-title::before {{
            content: "✍️";
            margin-right: 5px;
            font-size: 10pt;
        }}
        
        .signatures-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
        }}
        
        .signature-block {{
            text-align: center;
        }}
        
        .signature-line {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 2px;
            height: 30px;
            margin-bottom: 5px;
            position: relative;
        }}
        
        .signature-line::after {{
            content: "İmza";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #adb5bd;
            font-size: 7pt;
            font-style: italic;
        }}
        
        .signature-label {{
            font-size: 7pt;
            font-weight: 600;
            color: #495057;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 10px;
            margin-top: 0;
        }}
        
        .footer p {{
            margin: 2px 0;
            font-size: 7pt;
            opacity: 0.8;
        }}
        
        .footer strong {{
            color: #667eea;
        }}
        
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .document-container {{
                box-shadow: none;
                border-radius: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="document-container">
        <div class="header">
            <div class="company-name">{company_name}</div>
            <div class="document-title">Məzuniyyət Vərəqəsi</div>
        </div>
        
        <div class="content-wrapper">
            <div class="info-section">
                <div class="section-title">İşçi Məlumatları</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">İşçinin Adı</div>
                        <div class="info-value">{employee_data.get('name', '')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Vəzifəsi</div>
                        <div class="info-value">{employee_data.get('position', '')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Şöbəsi</div>
                        <div class="info-value">{employee_data.get('department', '')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">İşə Başlama</div>
                        <div class="info-value">{employee_data.get('hire_date', '')}</div>
                    </div>
                </div>
            </div>
            
            <div class="vacation-summary">
                <div class="summary-title">Məzuniyyət Xülasəsi</div>
                <div class="summary-grid">
                    <div class="summary-card">
                        <span class="summary-number">{total_vacation_days}</span>
                        <div class="summary-label">İllik Hüquq</div>
                    </div>
                    <div class="summary-card">
                        <span class="summary-number">{used_days}</span>
                        <div class="summary-label">İstifadə Edilmiş</div>
                    </div>
                    <div class="summary-card">
                        <span class="summary-number">{remaining_days}</span>
                        <div class="summary-label">Qalan</div>
                    </div>
                </div>
            </div>
            
            <div class="vacation-details">
                <div class="vacation-title">Məzuniyyət Detalları</div>
                
                <div class="date-grid">
                    <div class="date-card">
                        <div class="date-label">Başlanğıc</div>
                        <div class="date-value">{start_date_formatted}</div>
                    </div>
                    <div class="date-card">
                        <div class="date-label">Bitmə</div>
                        <div class="date-value">{end_date_formatted}</div>
                    </div>
                    <div class="date-card">
                        <div class="date-label">Müddət</div>
                        <div class="date-value">{duration} gün</div>
                    </div>
                </div>
                
                <div class="note-section">
                    <div class="note-label">Qeyd</div>
                    <div class="note-content">
                        {note if note else 'Qeyd yoxdur'}
                    </div>
                </div>
            </div>
            
            <div class="signatures-section">
                <div class="signatures-title">İmzalar</div>
                <div class="signatures-grid">
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-label">İşçi İmzası</div>
                    </div>
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-label">HR Meneceri</div>
                    </div>
                    <div class="signature-block">
                        <div class="signature-line"></div>
                        <div class="signature-label">Rəhbər İmzası</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Tarix: <strong>{today}</strong></p>
            <p>Bu sənəd avtomatik olaraq sistem tərəfindən yaradılmışdır</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_template

def generate_compact_vacation_html(employee_data: Dict[str, Any], vacation_data: Dict[str, Any], 
                                 company_name: str = "ŞİRKƏT ADI") -> str:
    """
    Yığcam məzuniyyət HTML formatı yaradır (1 səhifəyə sığır)
    """
    
    # Məzuniyyət günlərini hesabla
    total_vacation_days = employee_data.get('umumi_gun', 30)
    vacations = employee_data.get('goturulen_icazeler', [])
    
    # İstifadə edilmiş günləri düzgün hesabla
    used_days = calculate_vacation_days_used(vacations)
    remaining_days = total_vacation_days - used_days
    
    # Tarixləri format et
    start_date = vacation_data.get('start_date', '')
    end_date = vacation_data.get('end_date', '')
    note = vacation_data.get('note', '')
    
    # Müddəti hesabla
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration = (end_dt - start_dt).days + 1
            
            # Tarixləri Azərbaycan formatına çevir
            start_date_formatted = start_dt.strftime('%d.%m.%Y')
            end_date_formatted = end_dt.strftime('%d.%m.%Y')
        except:
            duration = 0
            start_date_formatted = start_date
            end_date_formatted = end_date
    else:
        duration = 0
        start_date_formatted = start_date
        end_date_formatted = end_date
    
    # Bugünkü tarixi format et
    today = datetime.now().strftime('%d.%m.%Y')
    
    html_template = f"""<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Məzuniyyət Vərəqəsi - {employee_data.get('name', 'İşçi')}</title>
    <style>
        @page {{
            size: A4;
            margin: 0.8cm;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            font-size: 9pt;
            line-height: 1.2;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 8px;
            margin-bottom: 10px;
        }}
        
        .company-name {{
            font-size: 12pt;
            font-weight: bold;
            margin-bottom: 2px;
        }}
        
        .document-title {{
            font-size: 10pt;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .content {{
            padding: 10px;
        }}
        
        .section {{
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 3px;
        }}
        
        .section-title {{
            font-size: 9pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .info-row {{
            display: flex;
            margin-bottom: 3px;
        }}
        
        .info-label {{
            font-weight: bold;
            width: 120px;
            font-size: 8pt;
            color: #666;
        }}
        
        .info-value {{
            flex: 1;
            border-bottom: 1px solid #ddd;
            padding-bottom: 1px;
            font-size: 9pt;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 5px;
            margin: 8px 0;
        }}
        
        .summary-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 5px;
            text-align: center;
        }}
        
        .summary-number {{
            font-size: 12pt;
            font-weight: bold;
            color: #667eea;
        }}
        
        .summary-label {{
            font-size: 7pt;
            color: #666;
            text-transform: uppercase;
        }}
        
        .vacation-details {{
            background: #fff3cd;
            border-left: 3px solid #ffc107;
            padding: 8px;
            margin: 8px 0;
            border-radius: 3px;
        }}
        
        .date-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 5px;
            margin: 5px 0;
        }}
        
        .date-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 2px;
            padding: 5px;
            text-align: center;
        }}
        
        .date-label {{
            font-size: 7pt;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 2px;
        }}
        
        .date-value {{
            font-size: 8pt;
            font-weight: bold;
        }}
        
        .note-section {{
            margin: 5px 0;
        }}
        
        .note-content {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 2px;
            padding: 5px;
            min-height: 30px;
            font-size: 8pt;
            font-style: italic;
        }}
        
        .signatures {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }}
        
        .signature-block {{
            text-align: center;
        }}
        
        .signature-line {{
            border-bottom: 1px solid #333;
            height: 25px;
            margin-bottom: 3px;
        }}
        
        .signature-label {{
            font-size: 7pt;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 5px;
            margin-top: 10px;
            font-size: 7pt;
        }}
        
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{company_name}</div>
        <div class="document-title">Məzuniyyət Vərəqəsi</div>
    </div>
    
    <div class="content">
        <div class="section">
            <div class="section-title">👤 İşçi Məlumatları</div>
            <div class="info-row">
                <div class="info-label">İşçinin Adı:</div>
                <div class="info-value">{employee_data.get('name', '')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Vəzifəsi:</div>
                <div class="info-value">{employee_data.get('position', '')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Şöbəsi:</div>
                <div class="info-value">{employee_data.get('department', '')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">İşə Başlama:</div>
                <div class="info-value">{employee_data.get('hire_date', '')}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 Məzuniyyət Xülasəsi</div>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-number">{total_vacation_days}</div>
                    <div class="summary-label">İllik Hüquq</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{used_days}</div>
                    <div class="summary-label">İstifadə Edilmiş</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{remaining_days}</div>
                    <div class="summary-label">Qalan</div>
                </div>
            </div>
        </div>
        
        <div class="vacation-details">
            <div class="section-title">📅 Məzuniyyət Detalları</div>
            <div class="date-grid">
                <div class="date-card">
                    <div class="date-label">Başlanğıc</div>
                    <div class="date-value">{start_date_formatted}</div>
                </div>
                <div class="date-card">
                    <div class="date-label">Bitmə</div>
                    <div class="date-value">{end_date_formatted}</div>
                </div>
                <div class="date-card">
                    <div class="date-label">Müddət</div>
                    <div class="date-value">{duration} gün</div>
                </div>
            </div>
            <div class="note-section">
                <div class="info-label">Qeyd:</div>
                <div class="note-content">
                    {note if note else 'Qeyd yoxdur'}
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">✍️ İmzalar</div>
            <div class="signatures">
                <div class="signature-block">
                    <div class="signature-line"></div>
                    <div class="signature-label">İşçi İmzası</div>
                </div>
                <div class="signature-block">
                    <div class="signature-line"></div>
                    <div class="signature-label">HR Meneceri</div>
                </div>
                <div class="signature-block">
                    <div class="signature-line"></div>
                    <div class="signature-label">Rəhbər İmzası</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>Tarix: <strong>{today}</strong> | Bu sənəd avtomatik olaraq sistem tərəfindən yaradılmışdır</p>
    </div>
</body>
</html>"""
    
    return html_template


def generate_all_vacations_html(employee_data: Dict[str, Any], company_name: str = "ŞİRKƏT ADI") -> str:
    """
    İşçinin bütün məzuniyyətlərini çap formatında hazırlayır
    
    Args:
        employee_data: İşçi məlumatları
        company_name: Şirkət adı
        
    Returns:
        HTML string
    """
    
    # Məzuniyyət məlumatlarını al
    total_vacation_days = employee_data.get('umumi_gun', 30)
    vacations = employee_data.get('goturulen_icazeler', [])
    
    print(f"DEBUG: Bütün məzuniyyətlər - İşçi: {employee_data.get('name')}")
    print(f"DEBUG: Ümumi günlər: {total_vacation_days}")
    print(f"DEBUG: Məzuniyyətlər sayı: {len(vacations)}")
    
    # İstifadə edilmiş günləri hesabla
    used_days = calculate_vacation_days_used(vacations)
    remaining_days = total_vacation_days - used_days
    
    # Bugünkü tarixi format et
    today = datetime.now().strftime('%d.%m.%Y')
    
    # Məzuniyyətləri HTML formatında hazırla
    vacations_html = ""
    if vacations:
        for i, vacation in enumerate(vacations, 1):
            if isinstance(vacation, dict):
                start_date = vacation.get('baslama', vacation.get('baslangic', ''))
                end_date = vacation.get('bitme', '')
                note = vacation.get('qeyd', '')
                status = vacation.get('status', 'Bitmiş')
                
                # Tarixləri format et - datetime.date və string formatlarını handle et
                if start_date:
                    try:
                        if hasattr(start_date, 'strftime'):  # datetime.date object
                            start_date_formatted = start_date.strftime('%d.%m.%Y')
                            start_date_str = start_date.strftime('%Y-%m-%d')
                        else:  # string
                            start_dt = datetime.strptime(str(start_date), '%Y-%m-%d')
                            start_date_formatted = start_dt.strftime('%d.%m.%Y')
                            start_date_str = str(start_date)
                    except:
                        start_date_formatted = str(start_date)
                        start_date_str = str(start_date)
                else:
                    start_date_formatted = ''
                    start_date_str = ''
                
                if end_date:
                    try:
                        if hasattr(end_date, 'strftime'):  # datetime.date object
                            end_date_formatted = end_date.strftime('%d.%m.%Y')
                            end_date_str = end_date.strftime('%Y-%m-%d')
                        else:  # string
                            end_dt = datetime.strptime(str(end_date), '%Y-%m-%d')
                            end_date_formatted = end_dt.strftime('%d.%m.%Y')
                            end_date_str = str(end_date)
                    except:
                        end_date_formatted = str(end_date)
                        end_date_str = str(end_date)
                else:
                    end_date_formatted = ''
                    end_date_str = ''
                
                # Müddəti yenidən hesabla (daha dəqiq)
                if start_date_str and end_date_str:
                    try:
                        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
                        calculated_duration = (end_dt - start_dt).days + 1
                        duration_formatted = f"{calculated_duration} gün"
                    except:
                        # Əgər hesablama uğursuz olarsa, database-dən gələn dəyəri istifadə et
                        duration = vacation.get('muddet', 0)
                        if isinstance(duration, str):
                            duration_formatted = duration
                        else:
                            duration_formatted = f"{duration} gün"
                else:
                    # Tarixlər yoxdursa, database-dən gələn dəyəri istifadə et
                    duration = vacation.get('muddet', 0)
                    if isinstance(duration, str):
                        duration_formatted = duration
                    else:
                        duration_formatted = f"{duration} gün"
                
                vacations_html += f"""
                <div class="vacation-item">
                    <div class="vacation-header">
                        <div class="vacation-number">{i}</div>
                        <div class="vacation-status">{status}</div>
                    </div>
                    <div class="vacation-details">
                        <div class="details-grid">
                            <div class="detail-card">
                                <div class="detail-label">Başlanğıc</div>
                                <div class="detail-value">{start_date_formatted}</div>
                            </div>
                            <div class="detail-card">
                                <div class="detail-label">Bitmə</div>
                                <div class="detail-value">{end_date_formatted}</div>
                            </div>
                            <div class="detail-card">
                                <div class="detail-label">Müddət</div>
                                <div class="detail-value">{duration_formatted}</div>
                            </div>
                        </div>
                        {f'<div class="vacation-note"><div class="note-label">Qeyd</div><div class="note-content">{note}</div></div>' if note else ''}
                    </div>
                </div>
                """
    else:
        vacations_html = '''
        <div class="no-vacations">
            <div class="no-vacations-icon">📅</div>
            <div class="no-vacations-text">Hələ məzuniyyət götürülməyib</div>
        </div>
        '''
    
    html_template = f"""<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bütün Məzuniyyətlər - {employee_data.get('name', 'İşçi')}</title>
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
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 25px 20px;
            margin-bottom: 0;
        }}
        
        .company-name {{
            font-size: 18pt;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .document-title {{
            font-size: 14pt;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            opacity: 0.95;
        }}
        
        .content-wrapper {{
            padding: 30px;
        }}
        
        .employee-info {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            border-left: 4px solid #667eea;
        }}
        
        .section-title {{
            font-size: 13pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}
        
        .section-title::before {{
            content: "👤";
            margin-right: 8px;
            font-size: 16pt;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .info-label {{
            font-weight: 600;
            color: #495057;
            font-size: 10pt;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .info-value {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 4px;
            padding: 10px 12px;
            font-weight: 500;
            color: #2c3e50;
            min-height: 40px;
            display: flex;
            align-items: center;
        }}
        
        .summary-section {{
            background: #e8f4f8;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 25px;
            border-left: 4px solid #17a2b8;
        }}
        
        .summary-title {{
            font-size: 13pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}
        
        .summary-title::before {{
            content: "📊";
            margin-right: 8px;
            font-size: 16pt;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
        }}
        
        .summary-card {{
            background: white;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .summary-number {{
            font-size: 20pt;
            font-weight: 700;
            color: #667eea;
            display: block;
            margin-bottom: 8px;
        }}
        
        .summary-label {{
            font-size: 10pt;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        .vacations-section {{
            margin-top: 30px;
        }}
        
        .vacations-title {{
            font-size: 13pt;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .vacations-title::before {{
            content: "📅";
            margin-right: 8px;
            font-size: 16pt;
        }}
        
        .vacation-item {{
            background: #fff3cd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #ffc107;
            page-break-inside: avoid;
            break-inside: avoid;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .vacation-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #f0c14b;
        }}
        
        .vacation-number {{
            background: #ffc107;
            color: white;
            font-weight: 700;
            font-size: 12pt;
            padding: 8px 12px;
            border-radius: 20px;
            margin-right: 15px;
            min-width: 40px;
            text-align: center;
        }}
        
        .vacation-status {{
            background: #28a745;
            color: white;
            font-size: 9pt;
            padding: 4px 8px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        .vacation-details {{
            background: white;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .details-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .detail-card {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e9ecef;
        }}
        
        .detail-label {{
            font-size: 9pt;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        
        .detail-value {{
            font-size: 11pt;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .vacation-note {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 12px;
            border-left: 3px solid #6c757d;
        }}
        
        .note-label {{
            font-size: 9pt;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        
        .note-content {{
            font-style: italic;
            color: #495057;
            font-size: 10pt;
        }}
        
        .no-vacations {{
            text-align: center;
            padding: 40px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px dashed #dee2e6;
        }}
        
        .no-vacations-icon {{
            font-size: 48pt;
            margin-bottom: 15px;
            opacity: 0.3;
        }}
        
        .no-vacations-text {{
            font-size: 12pt;
            color: #6c757d;
            font-style: italic;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            margin-top: 0;
        }}
        
        .footer p {{
            margin: 5px 0;
            font-size: 9pt;
            opacity: 0.8;
        }}
        
        .footer strong {{
            color: #667eea;
        }}
        
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .document-container {{
                box-shadow: none;
                border-radius: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="document-container">
        <div class="header">
            <div class="company-name">{company_name}</div>
            <div class="document-title">Məzuniyyət Tarixçəsi</div>
        </div>
        
        <div class="content-wrapper">
            <div class="employee-info">
                <div class="section-title">İşçi Məlumatları</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">İşçinin Adı</div>
                        <div class="info-value">{employee_data.get('name', '')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Vəzifəsi</div>
                        <div class="info-value">{employee_data.get('position', '')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Şöbəsi</div>
                        <div class="info-value">{employee_data.get('department', '')}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">İşə Başlama</div>
                        <div class="info-value">{employee_data.get('hire_date', '')}</div>
                    </div>
                </div>
            </div>
            
            <div class="summary-section">
                <div class="summary-title">Məzuniyyət Xülasəsi</div>
                <div class="summary-grid">
                    <div class="summary-card">
                        <span class="summary-number">{total_vacation_days}</span>
                        <div class="summary-label">İllik Hüquq</div>
                    </div>
                    <div class="summary-card">
                        <span class="summary-number">{used_days}</span>
                        <div class="summary-label">İstifadə Edilmiş</div>
                    </div>
                    <div class="summary-card">
                        <span class="summary-number">{remaining_days}</span>
                        <div class="summary-label">Qalan</div>
                    </div>
                </div>
            </div>
            
            <div class="vacations-section">
                <div class="vacations-title">Məzuniyyət Tarixçəsi</div>
                {vacations_html}
            </div>
        </div>
        
        <div class="footer">
            <p>Tarix: <strong>{today}</strong></p>
            <p>Bu sənəd avtomatik olaraq sistem tərəfindən yaradılmışdır</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_template

def generate_compact_all_vacations_html(employee_data: Dict[str, Any], company_name: str = "ŞİRKƏT ADI") -> str:
    """
    İşçinin bütün məzuniyyətlərini yığcam formatda hazırlayır (1 səhifəyə sığır)
    """
    
    # Məzuniyyət məlumatlarını al
    total_vacation_days = employee_data.get('umumi_gun', 30)
    vacations = employee_data.get('goturulen_icazeler', [])
    
    # İstifadə edilmiş günləri hesabla
    used_days = calculate_vacation_days_used(vacations)
    remaining_days = total_vacation_days - used_days
    
    # Bugünkü tarixi format et
    today = datetime.now().strftime('%d.%m.%Y')
    
    # Məzuniyyətləri yığcam HTML formatında hazırla
    vacations_html = ""
    if vacations:
        for i, vacation in enumerate(vacations, 1):
            if isinstance(vacation, dict):
                start_date = vacation.get('baslama', vacation.get('baslangic', ''))
                end_date = vacation.get('bitme', '')
                note = vacation.get('qeyd', '')
                status = vacation.get('status', 'Bitmiş')
                
                # Tarixləri format et
                if start_date:
                    try:
                        if hasattr(start_date, 'strftime'):
                            start_date_formatted = start_date.strftime('%d.%m.%Y')
                            start_date_str = start_date.strftime('%Y-%m-%d')
                        else:
                            start_dt = datetime.strptime(str(start_date), '%Y-%m-%d')
                            start_date_formatted = start_dt.strftime('%d.%m.%Y')
                            start_date_str = str(start_date)
                    except:
                        start_date_formatted = str(start_date)
                        start_date_str = str(start_date)
                else:
                    start_date_formatted = ''
                    start_date_str = ''
                
                if end_date:
                    try:
                        if hasattr(end_date, 'strftime'):
                            end_date_formatted = end_date.strftime('%d.%m.%Y')
                            end_date_str = end_date.strftime('%Y-%m-%d')
                        else:
                            end_dt = datetime.strptime(str(end_date), '%Y-%m-%d')
                            end_date_formatted = end_dt.strftime('%d.%m.%Y')
                            end_date_str = str(end_date)
                    except:
                        end_date_formatted = str(end_date)
                        end_date_str = str(end_date)
                else:
                    end_date_formatted = ''
                    end_date_str = ''
                
                # Müddəti yenidən hesabla
                if start_date_str and end_date_str:
                    try:
                        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
                        calculated_duration = (end_dt - start_dt).days + 1
                        duration_formatted = f"{calculated_duration} gün"
                    except:
                        duration = vacation.get('muddet', 0)
                        if isinstance(duration, str):
                            duration_formatted = duration
                        else:
                            duration_formatted = f"{duration} gün"
                else:
                    duration = vacation.get('muddet', 0)
                    if isinstance(duration, str):
                        duration_formatted = duration
                    else:
                        duration_formatted = f"{duration} gün"
                
                vacations_html += f"""
                <div class="vacation-row">
                    <div class="vacation-number">{i}</div>
                    <div class="vacation-dates">{start_date_formatted} - {end_date_formatted}</div>
                    <div class="vacation-duration">{duration_formatted}</div>
                    <div class="vacation-status">{status}</div>
                    <div class="vacation-note">{note if note else '-'}</div>
                </div>
                """
    else:
        vacations_html = '''
        <div class="no-vacations">
            <div class="no-vacations-text">Hələ məzuniyyət götürülməyib</div>
        </div>
        '''
    
    html_template = f"""<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bütün Məzuniyyətlər - {employee_data.get('name', 'İşçi')}</title>
    <style>
        @page {{
            size: A4;
            margin: 0.8cm;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            font-size: 9pt;
            line-height: 1.2;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 8px;
            margin-bottom: 10px;
        }}
        
        .company-name {{
            font-size: 12pt;
            font-weight: bold;
            margin-bottom: 2px;
        }}
        
        .document-title {{
            font-size: 10pt;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .content {{
            padding: 10px;
        }}
        
        .employee-info {{
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 3px;
        }}
        
        .section-title {{
            font-size: 9pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
        }}
        
        .info-row {{
            display: flex;
            margin-bottom: 2px;
        }}
        
        .info-label {{
            font-weight: bold;
            width: 80px;
            font-size: 8pt;
            color: #666;
        }}
        
        .info-value {{
            flex: 1;
            border-bottom: 1px solid #ddd;
            padding-bottom: 1px;
            font-size: 8pt;
        }}
        
        .summary-section {{
            background: #e8f4f8;
            border-left: 3px solid #17a2b8;
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 3px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 5px;
            margin: 5px 0;
        }}
        
        .summary-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 2px;
            padding: 5px;
            text-align: center;
        }}
        
        .summary-number {{
            font-size: 11pt;
            font-weight: bold;
            color: #667eea;
        }}
        
        .summary-label {{
            font-size: 6pt;
            color: #666;
            text-transform: uppercase;
        }}
        
        .vacations-section {{
            margin-top: 8px;
        }}
        
        .vacations-title {{
            font-size: 9pt;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
            padding-bottom: 3px;
            border-bottom: 1px solid #ddd;
        }}
        
        .vacations-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
        }}
        
        .table-header {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            margin-bottom: 2px;
        }}
        
        .header-row {{
            display: grid;
            grid-template-columns: 25px 120px 50px 50px 1fr;
            gap: 4px;
            padding: 6px 4px;
            border-bottom: 2px solid #667eea;
        }}
        
        .header-cell {{
            font-weight: bold;
            font-size: 7pt;
            color: #2c3e50;
            text-transform: uppercase;
            text-align: center;
        }}
        
        .table-header th {{
            padding: 4px;
            text-align: center;
            font-weight: bold;
            font-size: 7pt;
            color: #666;
            text-transform: uppercase;
        }}
        
        .vacation-row {{
            display: grid;
            grid-template-columns: 25px 120px 50px 50px 1fr;
            gap: 4px;
            padding: 4px;
            border-bottom: 1px solid #eee;
            align-items: center;
            min-height: 25px;
        }}
        
        .vacation-number {{
            background: #667eea;
            color: white;
            font-weight: bold;
            font-size: 7pt;
            padding: 2px;
            border-radius: 10px;
            text-align: center;
            min-width: 20px;
        }}
        
        .vacation-dates {{
            font-size: 8pt;
            font-weight: 500;
        }}
        
        .vacation-duration {{
            font-size: 8pt;
            font-weight: bold;
            color: #667eea;
            text-align: center;
        }}
        
        .vacation-status {{
            background: #28a745;
            color: white;
            font-size: 6pt;
            padding: 2px 4px;
            border-radius: 8px;
            text-align: center;
            text-transform: uppercase;
        }}
        
        .vacation-note {{
            font-size: 7pt;
            color: #666;
            font-style: italic;
            line-height: 1.2;
            word-wrap: break-word;
            max-height: 20px;
            overflow: hidden;
        }}
        
        .no-vacations {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 3px;
            border: 1px dashed #ddd;
        }}
        
        .no-vacations-text {{
            font-size: 9pt;
            color: #666;
            font-style: italic;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 5px;
            margin-top: 10px;
            font-size: 7pt;
        }}
        
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="company-name">{company_name}</div>
        <div class="document-title">Məzuniyyət Tarixçəsi</div>
    </div>
    
    <div class="content">
        <div class="employee-info">
            <div class="section-title">👤 İşçi Məlumatları</div>
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-label">Ad:</div>
                    <div class="info-value">{employee_data.get('name', '')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Vəzifə:</div>
                    <div class="info-value">{employee_data.get('position', '')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Şöbə:</div>
                    <div class="info-value">{employee_data.get('department', '')}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">İşə Başlama:</div>
                    <div class="info-value">{employee_data.get('hire_date', '')}</div>
                </div>
            </div>
        </div>
        
        <div class="summary-section">
            <div class="section-title">📊 Məzuniyyət Xülasəsi</div>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="summary-number">{total_vacation_days}</div>
                    <div class="summary-label">İllik Hüquq</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{used_days}</div>
                    <div class="summary-label">İstifadə Edilmiş</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{remaining_days}</div>
                    <div class="summary-label">Qalan</div>
                </div>
            </div>
        </div>
        
        <div class="vacations-section">
            <div class="vacations-title">📅 Məzuniyyət Tarixçəsi</div>
            <div class="table-header">
                <div class="header-row">
                    <div class="header-cell">№</div>
                    <div class="header-cell">Tarixlər</div>
                    <div class="header-cell">Müddət</div>
                    <div class="header-cell">Status</div>
                    <div class="header-cell">Qeyd</div>
                </div>
            </div>
            {vacations_html}
        </div>
    </div>
    
    <div class="footer">
        <p>Tarix: <strong>{today}</strong> | Bu sənəd avtomatik olaraq sistem tərəfindən yaradılmışdır</p>
    </div>
</body>
</html>"""
    
    return html_template


def get_employee_vacation_summary(employee_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    İşçinin məzuniyyət xülasəsini qaytarır
    
    Args:
        employee_data: İşçi məlumatları
        
    Returns:
        Dict: Məzuniyyət xülasəsi
    """
    total_vacation_days = employee_data.get('umumi_gun', 30)
    vacations = employee_data.get('goturulen_icazeler', [])
    
    # İstifadə edilmiş günləri düzgün hesabla
    used_days = calculate_vacation_days_used(vacations)
    remaining_days = total_vacation_days - used_days
    
    return {
        'total_days': total_vacation_days,
        'used_days': used_days,
        'remaining_days': remaining_days,
        'vacations': vacations
    }




def convert_html_to_pdf(html_content: str, output_path: str, use_weasyprint: bool = True) -> bool:
    """
    HTML məzmununu PDF-ə çevirir
    
    Args:
        html_content: HTML məzmunu
        output_path: PDF faylının yolu
        use_weasyprint: WeasyPrint istifadə etsin (yoxsa ReportLab)
        
    Returns:
        bool: Uğurlu olub-olmadığı
    """
    try:
        if use_weasyprint and WEASYPRINT_AVAILABLE:
            return _convert_with_weasyprint(html_content, output_path)
        elif REPORTLAB_AVAILABLE:
            return _convert_with_reportlab(html_content, output_path)
        else:
            raise Exception("PDF çevirmə kitabxanası quraşdırılmayıb!")
            
    except Exception as e:
        print(f"PDF çevirmə xətası: {e}")
        return False


def _convert_with_weasyprint(html_content: str, output_path: str) -> bool:
    """WeasyPrint ilə PDF çevirir"""
    try:
        HTML(string=html_content).write_pdf(output_path)
        return True
    except Exception as e:
        print(f"WeasyPrint xətası: {e}")
        return False


def _convert_with_reportlab(html_content: str, output_path: str) -> bool:
    """ReportLab ilə PDF çevirir (sadə versiya)"""
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12,
            textColor=colors.darkblue
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        story = []
        
        # HTML məzmununu parse et və PDF-ə çevir
        import re
        
        # Başlıq tap
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE)
        if title_match:
            story.append(Paragraph(title_match.group(1), title_style))
            story.append(Spacer(1, 20))
        
        # Məzmunu təmizlə və paragraf-lara böl
        clean_content = re.sub(r'<[^>]+>', '', html_content)
        clean_content = re.sub(r'\s+', ' ', clean_content)
        
        # Paragraf-lara böl
        paragraphs = clean_content.split('. ')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip() + '.', normal_style))
                story.append(Spacer(1, 6))
        
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"ReportLab xətası: {e}")
        return False


def show_print_preview_with_pdf(html_content: str, document_title: str = "Sənəd Önizləməsi") -> bool:
    """
    Çap önizləmə pəncərəsini göstərir (PDF dəstəyi ilə)
    
    Args:
        html_content: HTML məzmunu
        document_title: Sənəd başlığı
        
    Returns:
        bool: Uğurlu olub-olmadığı
    """
    try:
        from ui.print_preview_window import show_print_preview
        
        # Root window tap
        root = tk._default_root
        if root is None:
            root = tk.Tk()
            root.withdraw()  # Gizlə
        
        preview_window = show_print_preview(root, html_content, document_title)
        return preview_window is not None
        
    except Exception as e:
        print(f"Önizləmə pəncərəsi xətası: {e}")
        return False


