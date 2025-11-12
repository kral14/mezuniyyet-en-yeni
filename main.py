#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Məzuniyyət Sistemi - Əsas Giriş Faylı
Bu fayl proqramın əsas giriş nöqtəsidir
"""

import os
import sys

# src papkasını Python path-ə əlavə edirik
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Konsol mesajlarını susdurmaq və debug-u app daxilində yönətmək
try:
    from src.utils.debug_manager import configure_debug, setup_debug_print_intercept, debug_log
    # Konsolda print ON, bütün kateqoriyalar ON (həm konsolda həm debug pəncərəsində)
    configure_debug(console_output=True,
                    categories_on=['takvim','animasiya','database','ui','vacation','employee','signal','performance','umumi'])
    setup_debug_print_intercept()
    
    # Test mesajları göndər
    debug_log('umumi', 'Proqram başladıldı', '🚀')
    debug_log('database', 'Database bağlantısı hazırlanır', '🗄️')
    debug_log('ui', 'UI komponentləri yüklənir', '🖥️')
    
    # Print intercept test
    print("TEST: Print intercept işləyir")
    print("INFO:root:Test mesajı")
    print("DEBUG:root:Debug test mesajı")
    print("WARNING:root:Warning test mesajı")
    
    # Python logging-i aktiv saxla (konsolda görünsün)
    import logging
    # logging.disable(logging.CRITICAL)  # Söndürülüb
    
except Exception:
    # Debug manager import alınmasa belə proqram davam etsin
    pass

# PyInstaller mühitini yoxla
def is_pyinstaller():
    """PyInstaller EXE mühitində olub-olmadığımızı yoxlayır"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Log faylının yeri artıq UnifiedApplication-də göstərilir

# Əsas tətbiqi işə salırıq
if __name__ == "__main__":
    if is_pyinstaller():
        # PyInstaller EXE mühitində
        try:
            from src.core.main import main
            main()
        except ImportError as e:
            print(f"PyInstaller import xətası: {e}")
            print("Alternativ import yolu...")
            try:
                from core.main import main
                main()
            except ImportError as e2:
                print(f"Alternativ import xətası: {e2}")
                print("Proqram başladıla bilmədi!")
                input("Davam etmək üçün Enter basın...")
                sys.exit(1)
    else:
        # Normal Python mühitində
        try:
            from core.main import main
            main()
        except ImportError as e:
            print(f"Normal import xətası: {e}")
            print("Alternativ import yolu...")
            try:
                from src.core.main import main
                main()
            except ImportError as e2:
                print(f"Alternativ import xətası: {e2}")
                print("Proqram başladıla bilmədi!")
                input("Davam etmək üçün Enter basın...")
                sys.exit(1)