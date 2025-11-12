#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loading GIF Komponenti - Şəffaf və TAM MƏRKƏZDƏ
Test faylından əsas proqrama köçürüldü.
"""

import tkinter as tk
import os
import sys
import time
from PIL import Image, ImageTk

# Debug manager import
try:
    from utils.debug_manager import debug_log
except ImportError:
    try:
        from src.utils.debug_manager import debug_log
    except ImportError:
        def debug_log(*args, **kwargs):
            pass

class LoadingGif:
    """Şəffaf arxa fonda mərkəzləşdirilmiş loading GIF animasiyası"""
    
    def __init__(self):
        self.gif_frames = []
        self.current_frame = 0
        self.gif_label = None
        self.after_id = None
        self.overlay = None
        self.loading_active = False
        self.animation_speed = 100  # ms
        self.gif_path = None
        self.master_root = None  # Toplevel üçün real root (exe-də _default_root None ola bilər)
        self._shown_at_ms = 0  # show çağırıldığı zaman (ms)
        self.min_visible_ms = 0  # Minimum görünmə müddəti - silindi (animasiya dərhal gizlənə bilər)
        
    def load_gif(self, gif_path):
        """GIF faylını yükləyir və frame-lərə bölür"""
        try:
            if not os.path.exists(gif_path):
                return False
            
            # GIF-in path-ini saxla
            self.gif_path = gif_path
            
            image = Image.open(gif_path)
            self.gif_frames = []
            
            try:
                while True:
                    self.gif_frames.append(ImageTk.PhotoImage(image.copy()))
                    image.seek(len(self.gif_frames))
            except EOFError:
                pass
            
            return len(self.gif_frames) > 0
            
        except Exception as e:
            print(f"Loading GIF xətası: {e}")
            return False
    
    def show(self, parent_window=None, text="Gözləyin..."):
        """Loading animasiyasını göstərir"""
        print("🟢 DEBUG: LoadingGif.show() çağırıldı")
        print(f"🟢 DEBUG: parent_window = {parent_window}")
        print(f"🟢 DEBUG: text = {text}")
        print(f"🟢 DEBUG: loading_active = {self.loading_active}")
        
        if self.loading_active:
            print("⚠️ DEBUG: loading_active = True, return")
            return
        
        # Əgər GIF yüklənməyibsə, yüklə
        print(f"🟢 DEBUG: gif_frames count = {len(self.gif_frames)}")
        if not self.gif_frames:
            # Default GIF path - EXE və normal rejim üçün
            gif_path = None
            
            if getattr(sys, 'frozen', False):
                # PyInstaller EXE mode - animasiyalar are in root animasiyalar folder
                base_path = getattr(sys, '_MEIPASS', None)
                if base_path:
                    # Birinci yol: animasiyalar/yuklenme/Loading.gif
                    gif_path = os.path.join(base_path, 'animasiyalar', 'yuklenme', 'Loading.gif')
                    if not os.path.exists(gif_path):
                        # İkinci yol: src/animasiyalar/yuklenme/Loading.gif (fallback)
                        gif_path = os.path.join(base_path, 'src', 'animasiyalar', 'yuklenme', 'Loading.gif')
                    if not os.path.exists(gif_path):
                        # Üçüncü yol: EXE faylının yanında
                        exe_dir = os.path.dirname(sys.executable) if hasattr(sys, 'executable') else None
                        if exe_dir:
                            gif_path = os.path.join(exe_dir, 'animasiyalar', 'yuklenme', 'Loading.gif')
            else:
                # Normal Python mode
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                gif_path = os.path.join(base_path, 'src', 'animasiyalar', 'yuklenme', 'Loading.gif')
            
            print(f"🟢 DEBUG: GIF path = {gif_path}")
            print(f"🟢 DEBUG: GIF path exists = {os.path.exists(gif_path) if gif_path else False}")
            
            if not gif_path or not self.load_gif(gif_path):
                print("❌ DEBUG: Loading GIF yüklənə bilmədi")
                # GIF yüklənməsə belə animasiya göstərməyə çalışma - return
                return
            print(f"✅ DEBUG: GIF yükləndi, {len(self.gif_frames)} frame")
        
        # Parent window tap (Frame verilibsə həqiqi root-u çıxart)
        root = None
        if parent_window is not None:
            try:
                root = parent_window.winfo_toplevel()
            except Exception:
                root = parent_window
        if root is None:
            root = tk._default_root
        print(f"🟢 DEBUG: root = {root}")
        self.master_root = root
        
        self.loading_active = True
        self.current_frame = 0
        print("🟢 DEBUG: loading_active = True set edildi")
        # Görünmə start timestamp
        self._shown_at_ms = int(time.time() * 1000)
        
        # Şəffaf overlay pəncərəsi - PROQRAM PƏNCƏRƏSİNƏ BAĞLI
        print("🟢 DEBUG: Overlay pəncərəsi yaradılır...")
        self.overlay = tk.Toplevel(root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes('-topmost', True)
        
        # PROQRAM PƏNCƏRƏSİNƏ BAĞLA - modal olmadan
        self.overlay.transient(root)  # Parent pəncərəyə bağla
        # grab_set() istifadə etmirik - modal pəncərə yaradır və animasiyanı gizlədir
        
        # PROQRAM PƏNCƏRƏSİNİN HƏRƏKƏTİNİ İZLƏ - animasiyanı birlikdə hərəkət etdir
        self._setup_window_movement_sync(root)
        
        # PROQRAM STATE-İNİ İZLƏ - minimize edildikdə animasiyanı gizlə
        self._setup_window_state_monitoring(root)
        
        print("✅ DEBUG: Overlay pəncərəsi yaradıldı və proqrama bağlandı")
        
        # GIF ölçüsünü təxmin et
        gif_width = 200
        gif_height = 200
        
        # Pəncərəni PROQRAM PƏNCƏRƏSİNİN MƏRKƏZİNDƏ yerləşdir
        try:
            # Parent pəncərənin mərkəzini tap
            parent_x = root.winfo_x()
            parent_y = root.winfo_y()
            parent_width = root.winfo_width()
            parent_height = root.winfo_height()
            
            # Parent pəncərənin mərkəzində yerləşdir
            x = parent_x + (parent_width // 2) - (gif_width // 2)
            y = parent_y + (parent_height // 2) - (gif_height // 2)
            
            # Ekran həddlərini yoxla
            screen_width = self.overlay.winfo_screenwidth()
            screen_height = self.overlay.winfo_screenheight()
            x = max(0, min(x, screen_width - gif_width))
            y = max(0, min(y, screen_height - gif_height))
            
            self.overlay.geometry(f"{gif_width}x{gif_height}+{x}+{y}")
            print(f"🟢 DEBUG: Overlay geometry (parent center): {gif_width}x{gif_height}+{x}+{y}")
            
        except Exception as e:
            # Fallback: ekran mərkəzində
            screen_width = self.overlay.winfo_screenwidth()
            screen_height = self.overlay.winfo_screenheight()
            x = (screen_width // 2) - (gif_width // 2)
            y = (screen_height // 2) - (gif_height // 2)
            self.overlay.geometry(f"{gif_width}x{gif_height}+{x}+{y}")
            print(f"🟢 DEBUG: Overlay geometry (screen center fallback): {gif_width}x{gif_height}+{x}+{y}")
            print(f"⚠️ DEBUG: Parent center calculation xətası: {e}")
        
        # Frame-i ŞƏFFAF et
        try:
            self.overlay.attributes('-transparentcolor', 'white')
            self.overlay.configure(bg='white')
            print("✅ DEBUG: transparentcolor attribute set edildi")
        except Exception as e:
            self.overlay.configure(bg='white')
            print(f"⚠️ DEBUG: transparentcolor xətası: {e}")
        
        # GIF label - şəffaf arxa fon
        print(f"🟢 DEBUG: GIF label yaradılır, {len(self.gif_frames)} frame mövcuddur")
        self.gif_label = tk.Label(self.overlay, image=self.gif_frames[0], 
                                 bg='white', borderwidth=0, highlightthickness=0)
        self.gif_label.pack()
        print("✅ DEBUG: GIF label yaradıldı və pack edildi")
        
        # Overlay-i göstər - əvvəlcə lazy update, sonra tam update
        self.overlay.update_idletasks()
        self.overlay.update()  # Force UI update
        
        # ANIMASIYANIN GÖRÜNMƏSİNİ TƏMİN ET
        self.overlay.lift()  # Pəncərəni önə gətir
        self.overlay.focus_force()  # Focus ver
        
        # EXE-də animasiyanın görünməməsi problemini həll et
        try:
            # Pəncərəni məcburi göstər
            self.overlay.deiconify()  # Minimize edilibsə bərpa et
            self.overlay.state('normal')  # Normal state-ə keçir
            self.overlay.attributes('-topmost', True)  # Yenidən topmost et
            
            # Bir az gözlə və yenidən yoxla
            self.overlay.after(50, lambda: self._ensure_visibility())
        except Exception as e:
            print(f"⚠️ DEBUG: Visibility ensure xətası: {e}")
        
        print(f"✅ DEBUG: Overlay update edildi, winfo_exists={self.overlay.winfo_exists()}")
        print(f"✅ DEBUG: Overlay geometry: {self.overlay.geometry()}")
        print(f"✅ DEBUG: Overlay state: {self.overlay.state()}")
        
        # Animasiya başlat
        print("🟢 DEBUG: Animasiya başladılır...")
        self._animate()
        print("✅ DEBUG: show() tamamlandı")
    
    def _animate(self):
        """GIF animasiyasını işə salır"""
        import time
        frame_start_time = time.time()  # Frame başlama zamanı
        
        print(f"🔵 DEBUG _animate çağırıldı - loading_active={self.loading_active}, frame={self.current_frame}")
        
        # EXE-də animasiyanı durdurmaq üçün loading_active yoxlamasını gücləndir
        if not self.loading_active:
            print("⚠️ DEBUG _animate: loading_active = False - animasiya durduruldu")
            debug_log('animasiya', 'loading_active=False - DURDURULDU', '⚠️')
            # Animasiya bitməlidir - after_id-ni clear et
            self.after_id = None
            return
        
        try:
            if self.gif_label and self.current_frame < len(self.gif_frames):
                # Frame-i güncelle
                self.gif_label.config(image=self.gif_frames[self.current_frame])
                
                # Hər frame-i log et (şərhə al - çox debug mesajı)
                # print(f"🎬 Frame {self.current_frame}/{len(self.gif_frames)} gösterildi")
                # debug_log('animasiya', f'Frame {self.current_frame}/{len(self.gif_frames)}', '🎬')
                
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                
                # Növbəti frame üçün callback planla - ANCAQ loading_active True olduqda
                if self.loading_active:
                    scheduler = self.overlay if (self.overlay and self.overlay.winfo_exists()) else self.master_root
                    if scheduler and scheduler.winfo_exists():
                        print(f"✅ DEBUG _animate: after() çağırılır, növbəti frame: {self.current_frame}")
                        self.after_id = scheduler.after(self.animation_speed, self._animate)
                    else:
                        print("❌ DEBUG _animate: Scheduler mövcud deyil!")
                        self.after_id = None
                else:
                    print(f"❌ DEBUG _animate: Overlay artıq yoxdur və ya loading_active False! overlay={self.overlay}, loading_active={self.loading_active}")
                    debug_log('animasiya', f'Overlay yoxdur və ya loading_active=False - DURDURULDU', '❌')
                    self.after_id = None
            else:
                print(f"⚠️ DEBUG _animate: Şərtlər yerinə yetirilməyib - gif_label={bool(self.gif_label)}, current_frame={self.current_frame}, frames={len(self.gif_frames)}")
        except Exception as e:
            print(f"❌ DEBUG _animate xətası: {e}")
            import traceback
            traceback.print_exc()
            debug_log('animasiya', f'Xəta: {e}', '❌')
            self.after_id = None
    
    def hide(self):
        """Loading animasiyasını gizlədir"""
        print("🔴 DEBUG hide(): hide() çağırıldı")
        
        if not self.loading_active:
            print("⚠️ DEBUG hide(): loading_active zaten False, heç nə etmək lazım deyil")
            return
        
        # Minimum görünmə müddəti silindi - dərhal gizlət
        self._perform_hide()

    def _perform_hide(self):
        """Gizlətməni faktiki icra edir (daxili)"""
        print("🛑 DEBUG _perform_hide(): icra edilir")
        print("🛑 DEBUG hide(): loading_active = False edilir")
        
        # EXE-də animasiyanın dayanması üçün ƏVVƏL after_id-ni cancel et (loading_active dəyişmədən əvvəl)
        if self.after_id:
            print(f"⏹️ DEBUG hide(): after_id={self.after_id} cancel edilir")
            try:
                # Overlay mövcud olsa da, olmasa da cancel etməyə çalış
                scheduler = None
                if self.overlay and self.overlay.winfo_exists():
                    scheduler = self.overlay
                elif self.master_root and self.master_root.winfo_exists():
                    scheduler = self.master_root
                elif tk._default_root and tk._default_root.winfo_exists():
                    scheduler = tk._default_root
                if scheduler:
                    scheduler.after_cancel(self.after_id)
                    print("✅ DEBUG hide(): after_id cancel edildi (scheduler)")
            except Exception as e:
                print(f"⚠️ DEBUG hide(): after_cancel xətası: {e}")
        
        # İndi loading_active-i False et (after_id artıq cancel edildi)
        self.loading_active = False
        self._shown_at_ms = 0
        
        # Overlay pəncərəsini bağla
        if self.overlay:
            print("🗑️ DEBUG hide(): Overlay destroy edilir")
            try:
                if self.overlay.winfo_exists():
                    self.overlay.destroy()
                    print("✅ DEBUG hide(): Overlay destroy edildi")
                else:
                    print("⚠️ DEBUG hide(): Overlay artıq destroy edilib")
            except Exception as e:
                print(f"⚠️ DEBUG hide(): destroy xətası: {e}")
        
        # Variables-i clear et
        self.overlay = None
        self.gif_label = None
        self.after_id = None
        
        # EXE-də UI refresh etmək üçün force update
        try:
            root = tk._default_root
            if root:
                root.update_idletasks()
                root.update()
                print("✅ DEBUG hide(): UI update edildi")
        except Exception as e:
            print(f"⚠️ DEBUG hide(): UI update xətası: {e}")
        
        print("🏁 DEBUG hide(): hide() tamamlandı")
    
    def _ensure_visibility(self):
        """Animasiyanın görünməsini təmin edir"""
        if not self.loading_active or not self.overlay:
            return
        
        try:
            # Pəncərə mövcuddursa və görünmürsə məcburi göstər
            if self.overlay.winfo_exists():
                if not self.overlay.winfo_viewable():
                    print("🔧 DEBUG: Overlay görünmür, məcburi göstərilir")
                    self.overlay.deiconify()
                    self.overlay.lift()
                    self.overlay.attributes('-topmost', True)
                
                # State-i yoxla
                state = self.overlay.state()
                if state != 'normal':
                    print(f"🔧 DEBUG: Overlay state={state}, normal-ə keçirilir")
                    self.overlay.state('normal')
                
                print(f"✅ DEBUG: Visibility ensure tamamlandı - state={self.overlay.state()}, viewable={self.overlay.winfo_viewable()}")
        except Exception as e:
            print(f"⚠️ DEBUG: _ensure_visibility xətası: {e}")
    
    def _setup_window_movement_sync(self, parent_window):
        """Proqram pəncərəsinin hərəkətini izləyir və animasiyanı birlikdə hərəkət etdirir"""
        try:
            # Parent pəncərənin mövqeyini izlə
            def sync_window_position():
                if not self.loading_active or not self.overlay:
                    return
                
                try:
                    if parent_window and parent_window.winfo_exists():
                        # Parent pəncərənin mövqeyini al
                        parent_x = parent_window.winfo_x()
                        parent_y = parent_window.winfo_y()
                        parent_width = parent_window.winfo_width()
                        parent_height = parent_window.winfo_height()
                        
                        # Animasiyanı parent pəncərənin mərkəzində yerləşdir
                        gif_width = 200
                        gif_height = 200
                        x = parent_x + (parent_width // 2) - (gif_width // 2)
                        y = parent_y + (parent_height // 2) - (gif_height // 2)
                        
                        # Ekran həddlərini yoxla
                        screen_width = self.overlay.winfo_screenwidth()
                        screen_height = self.overlay.winfo_screenheight()
                        x = max(0, min(x, screen_width - gif_width))
                        y = max(0, min(y, screen_height - gif_height))
                        
                        # Animasiyanın mövqeyini yenilə
                        current_geometry = self.overlay.geometry()
                        new_geometry = f"{gif_width}x{gif_height}+{x}+{y}"
                        
                        if current_geometry != new_geometry:
                            self.overlay.geometry(new_geometry)
                            print(f"🔄 DEBUG: Animasiya mövqeyi yeniləndi: {new_geometry}")
                    
                    # 50ms sonra yenidən yoxla (daha hamar izləmə)
                    if self.loading_active and self.overlay and self.overlay.winfo_exists():
                        self.overlay.after(50, sync_window_position)
                        
                except Exception as e:
                    print(f"⚠️ DEBUG: Window movement sync xətası: {e}")
            
            # Sync-i başlat
            sync_window_position()
            
            # REAL-TIME EVENT BINDING - pəncərə hərəkət etdikdə dərhal reaksiya ver
            try:
                # Parent pəncərəyə event listener əlavə et
                parent_window.bind('<Configure>', lambda e: self._on_parent_configure(e))
                print("✅ DEBUG: Real-time event binding əlavə edildi")
            except Exception as bind_error:
                print(f"⚠️ DEBUG: Event binding xətası: {bind_error}")
            
            print("✅ DEBUG: Window movement sync başladıldı")
            
        except Exception as e:
            print(f"⚠️ DEBUG: Window movement sync setup xətası: {e}")
    
    def _on_parent_configure(self, event):
        """Parent pəncərə hərəkət etdikdə çağırılır"""
        if not self.loading_active or not self.overlay:
            return
        
        try:
            # Event-dən parent pəncərəni al
            parent_window = event.widget
            
            # Parent pəncərənin mövqeyini al
            parent_x = parent_window.winfo_x()
            parent_y = parent_window.winfo_y()
            parent_width = parent_window.winfo_width()
            parent_height = parent_window.winfo_height()
            
            # Animasiyanı parent pəncərənin mərkəzində yerləşdir
            gif_width = 200
            gif_height = 200
            x = parent_x + (parent_width // 2) - (gif_width // 2)
            y = parent_y + (parent_height // 2) - (gif_height // 2)
            
            # Ekran həddlərini yoxla
            screen_width = self.overlay.winfo_screenwidth()
            screen_height = self.overlay.winfo_screenheight()
            x = max(0, min(x, screen_width - gif_width))
            y = max(0, min(y, screen_height - gif_height))
            
            # Animasiyanın mövqeyini dərhal yenilə
            new_geometry = f"{gif_width}x{gif_height}+{x}+{y}"
            self.overlay.geometry(new_geometry)
            # Overlay-in həmişə görünür qalması üçün önə qaldır
            try:
                self.overlay.lift()
                self.overlay.attributes('-topmost', True)
            except Exception:
                pass
            print(f"⚡ DEBUG: Real-time animasiya mövqeyi: {new_geometry}")
            
        except Exception as e:
            print(f"⚠️ DEBUG: _on_parent_configure xətası: {e}")
    
    def _setup_window_state_monitoring(self, parent_window):
        """Proqram pəncərəsinin state-ini izləyir və minimize edildikdə animasiyanı gizlədir"""
        try:
            # Parent pəncərənin state-ini izlə
            def check_window_state():
                if not self.loading_active:
                    return
                
                try:
                    # Parent pəncərə minimize edilibsə animasiyanı gizlə
                    if parent_window and parent_window.winfo_exists():
                        state = parent_window.state()
                        if state == 'iconic':  # Minimize edilib
                            print("🔴 DEBUG: Parent pəncərə minimize edildi, animasiya gizlədirilir")
                            self.hide()
                            return
                        
                        # NOTE: Hərəkət zamanı qısa müddət viewable=False ola bilər.
                        # Artıq buna görə gizlətmirik; yalnız minimize olduqda gizlədirik.
                    
                    # 100ms sonra yenidən yoxla
                    if self.loading_active and self.overlay and self.overlay.winfo_exists():
                        self.overlay.after(100, check_window_state)
                        
                except Exception as e:
                    print(f"⚠️ DEBUG: Window state monitoring xətası: {e}")
            
            # Monitoring-i başlat
            check_window_state()
            print("✅ DEBUG: Window state monitoring başladıldı")
            
        except Exception as e:
            print(f"⚠️ DEBUG: Window state monitoring setup xətası: {e}")

# Global instance
_loading_gif = None

def get_loading_gif():
    """Global loading GIF instance qaytarır"""
    global _loading_gif
    if _loading_gif is None:
        _loading_gif = LoadingGif()
    return _loading_gif

def show_loading(parent_window=None, text="Gözləyin..."):
    """Loading göstərir"""
    print("🔵 DEBUG: show_loading() çağırıldı")
    loading = get_loading_gif()
    print(f"🔵 DEBUG: loading instance = {loading}")
    loading.show(parent_window, text)

def hide_loading():
    """Loading gizlədir"""
    get_loading_gif().hide()

