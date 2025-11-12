# -*- coding: utf-8 -*-
"""
Text formatting utilities for the application
"""

import re
import logging

def format_name(name):
    """
    Adı düzgün formatda qaytarır (İlk hərf böyük, qalan hərflər kiçik)
    
    Args:
        name (str): Formatlanacaq ad
        
    Returns:
        str: Formatlanmış ad
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Boşluqları təmizlə və kiçik hərflərə çevir
    name = name.strip().lower()
    
    # Boş string yoxla
    if not name:
        return ""
    
    # Azərbaycan hərflərini dəstəklə
    # İlk hərfi böyük et
    formatted_name = name[0].upper() + name[1:]
    
    # Boşluqdan sonra hər hərfi böyük et (soyad üçün)
    words = formatted_name.split()
    formatted_words = []
    
    for word in words:
        if word:
            # İlk hərfi böyük, qalan hərfləri kiçik
            formatted_word = word[0].upper() + word[1:].lower()
            formatted_words.append(formatted_word)
    
    return ' '.join(formatted_words)

def format_full_name(first_name, last_name, father_name=None):
    """
    Tam adı düzgün formatda qaytarır
    
    Args:
        first_name (str): Ad
        last_name (str): Soyad
        father_name (str, optional): Ata adı
        
    Returns:
        str: Formatlanmış tam ad
    """
    parts = []
    
    if first_name:
        parts.append(format_name(first_name))
    
    if last_name:
        parts.append(format_name(last_name))
    
    if father_name:
        parts.append(format_name(father_name))
    
    return ' '.join(parts)

def format_employee_display_name(employee_data):
    """
    İşçi məlumatlarından göstərmə üçün formatlanmış ad yaradır
    
    Args:
        employee_data (dict): İşçi məlumatları
        
    Returns:
        str: Formatlanmış göstərmə adı
    """
    if not employee_data:
        return ""
    
    # Əvvəlcə name sahəsini yoxla
    if 'name' in employee_data and employee_data['name']:
        return format_name(employee_data['name'])
    
    # Əgər name yoxdursa, first_name və last_name-dən yarat
    first_name = employee_data.get('first_name', '')
    last_name = employee_data.get('last_name', '')
    
    if first_name or last_name:
        return format_full_name(first_name, last_name)
    
    return ""

def format_username(first_name, last_name):
    """
    İstifadəçi adını formatlayır (kiçik hərflərlə, nöqtə ilə)
    
    Args:
        first_name (str): Ad
        last_name (str): Soyad
        
    Returns:
        str: Formatlanmış istifadəçi adı
    """
    if not first_name and not last_name:
        return ""
    
    first = format_name(first_name).lower() if first_name else ""
    last = format_name(last_name).lower() if last_name else ""
    
    if first and last:
        return f"{first}.{last}"
    elif first:
        return first
    elif last:
        return last
    
    return ""

def clean_and_format_text(text):
    """
    Mətn təmizləyir və formatlayır
    
    Args:
        text (str): Təmizlənəcək mətn
        
    Returns:
        str: Təmizlənmiş və formatlanmış mətn
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Artıq boşluqları təmizlə
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Formatla
    return format_name(text)

