# ui/loading_animation.py - Loading animasiyası komponenti

import tkinter as tk
from tkinter import ttk
import math
import logging
import random
import time

class LoadingAnimation:
    def __init__(self, parent_container):
        self.parent_container = parent_container
        self.loading_frame = None
        self.loading_canvas = None
        self.elements = []
        self.particles = []
        self.animation_time = 0
        self.animation_running = False
        self.canvas_width = 0
        self.canvas_height = 0
        self.last_resize_time = 0
        
    def show(self):
        """Loading animasiyasını göstərir."""
        print("🔵 DEBUG: LoadingAnimation.show() başladı")
        print(f"🔵 DEBUG: Parent container ölçüsü: {self.parent_container.winfo_width()}x{self.parent_container.winfo_height()}")
        
        # Mövcud widgetləri təmizləyirik
        print("🔵 DEBUG: Mövcud widgetlər təmizlənir")
        for widget in self.parent_container.winfo_children():
            widget.destroy()
        
        # Loading frame yaradırıq
        print("🔵 DEBUG: Loading frame yaradılır")
        self.loading_frame = ttk.Frame(self.parent_container)
        self.loading_frame.pack(expand=True, fill="both")
        
        # Loading canvas yaradırıq
        print("🔵 DEBUG: Loading canvas yaradılır")
        self.loading_canvas = tk.Canvas(self.loading_frame, highlightthickness=0, bg='white')
        self.loading_canvas.pack(expand=True, fill="both")
        
        # Canvas ölçüsünü alırıq
        print("🔵 DEBUG: Canvas ölçüsü alınır")
        self.loading_canvas.update_idletasks()
        self.canvas_width = self.loading_canvas.winfo_width()
        self.canvas_height = self.loading_canvas.winfo_height()
        print(f"🔵 DEBUG: Canvas ölçüsü: {self.canvas_width}x{self.canvas_height}")
        
        # Ağ arxa fon yaradırıq
        print("🔵 DEBUG: Ağ arxa fon yaradılır")
        self.create_white_background()
        
        # Animasiya parametrləri
        print("🔵 DEBUG: Animasiya parametrləri təyin edilir")
        self.animation_time = 0
        self.elements = []
        self.particles = []
        self.last_resize_time = time.time()
        
        # Elementləri yaradırıq
        print("🔵 DEBUG: Animasiya elementləri yaradılır")
        self.create_animation_elements()
        
        # Loading mətni
        print("🔵 DEBUG: Loading mətni yaradılır")
        self.create_loading_text()
        
        # Container-i pack edirik
        print("🔵 DEBUG: Container pack edilir")
        self.parent_container.pack(fill="both", expand=True)
        
        # Animasiya başladırıq
        print("🔵 DEBUG: Animasiya başladılır")
        self.animation_running = True
        self.animate_elements()
        print("🔵 DEBUG: LoadingAnimation.show() tamamlandı")

    def create_white_background(self):
        """Ağ arxa fon yaradır."""
        # Sadə ağ arxa fon
        self.loading_canvas.configure(bg='white')

    def create_animation_elements(self):
        """Animasiya elementlərini yaradır."""
        # Mərkəz koordinatları
        center_x = self.canvas_width // 2
        center_y = self.canvas_height // 2
        
        # Responsive ölçülər
        min_size = min(self.canvas_width, self.canvas_height)
        base_radius = min_size // 8
        element_size = min_size // 50
        
        # Daha çox rəng
        colors = [
            '#FF6B9D',  # Çəhrayı
            '#4ECDC4',  # Turkuaz
            '#45B7D1',  # Mavi
            '#96CEB4',  # Yaşıl
            '#FFE66D',  # Sarı
            '#FF8A80',  # Qırmızı
            '#9575CD',  # Bənövşəyi
            '#4DB6AC',  # Yaşıl-mavi
            '#FFB74D',  # Narıncı
            '#81C784',  # Yaşıl
            '#64B5F6',  # Mavi
            '#F06292',  # Çəhrayı
            '#FFD54F',  # Sarı
            '#A1887F',  # Qəhvəyi
            '#90A4AE'   # Boz
        ]
        
        # Əsas spiral animasiya elementləri
        for i in range(10):  # Daha çox element
            angle = (i * 36) * (math.pi / 180)  # 36 dərəcə aralıqla
            radius = base_radius + i * (base_radius // 4)
            
            element = {
                'type': 'circle',
                'x': center_x + radius * math.cos(angle),
                'y': center_y + radius * math.sin(angle),
                'radius': element_size + (i % 3) * (element_size // 2),
                'color': colors[i % len(colors)],
                'angle': angle,
                'base_radius': radius,
                'speed': 0.02 + (i * 0.005),  # Fərqli sürətlər
                'phase': i * 0.3,
                'base_element_size': element_size,
                'created_time': time.time(),
                'life': 1.0,
                'fill_type': i % 2  # 0: dolu, 1: boş
            }
            self.elements.append(element)
        
        # Dönən halqa elementləri
        for i in range(8):  # Daha çox halqa
            angle = (i * 45) * (math.pi / 180)
            radius = base_radius * 2.2
            
            element = {
                'type': 'ring',
                'x': center_x + radius * math.cos(angle),
                'y': center_y + radius * math.sin(angle),
                'size': element_size * 1.8,
                'color': colors[i % len(colors)],
                'angle': angle,
                'radius': radius,
                'speed': 0.025 + (i * 0.003),  # Fərqli sürətlər
                'phase': i * 0.4,
                'base_element_size': element_size * 1.8,
                'created_time': time.time(),
                'life': 1.0,
                'fill_type': i % 2  # 0: dolu, 1: boş
            }
            self.elements.append(element)

    def create_loading_text(self):
        """Loading mətni yaradır."""
        font_size = min(self.canvas_width, self.canvas_height) // 25
        self.loading_text = self.loading_canvas.create_text(
            self.canvas_width//2, self.canvas_height//2 + (min(self.canvas_width, self.canvas_height) // 4), 
            text="Yüklənir...", 
            font=('Segoe UI', font_size, 'bold'), 
            fill='#333333'
        )

    def create_pulse_effect(self, x, y, color):
        """Pulse effekti yaradır."""
        # Responsive sürət - pəncərə ölçüsünə uyğun
        min_size = min(self.canvas_width, self.canvas_height)
        base_speed = min_size / 200  # Pəncərə ölçüsünə uyğun sürət
        
        for _ in range(4):  # Daha çox hissəcik
            size = random.uniform(2, 6)  # Daha böyük hissəciklər
            speed = random.uniform(0.8, 2.0) * base_speed  # Responsive sürət
            
            particle = {
                'x': x,
                'y': y,
                'vx': (random.random() - 0.5) * speed,
                'vy': (random.random() - 0.5) * speed,
                'size': size,
                'color': color,
                'life': 4.0,  # Çox uzun həyat
                'decay': random.uniform(0.05, 0.1),  # Daha yavaş azalma
                'type': 'pulse',
                'created_time': time.time(),
                'base_speed': base_speed  # Responsive sürəti saxlayırıq
            }
            self.particles.append(particle)

    def animate_elements(self):
        """Elementləri animasiya edir."""
        if not self.animation_running:
            return
            
        if not self.loading_canvas or not self.loading_canvas.winfo_exists():
            return
            
        try:
            # Canvas ölçüsünü yenidən alırıq
            self.loading_canvas.update_idletasks()
            new_width = self.loading_canvas.winfo_width()
            new_height = self.loading_canvas.winfo_height()
            
            current_time = time.time()
            
            # Ölçü dəyişibsə tam yenidən başladırıq
            if new_width != self.canvas_width or new_height != self.canvas_height:
                self.canvas_width = new_width
                self.canvas_height = new_height
                self.last_resize_time = current_time
                
                if self.canvas_width > 1 and self.canvas_height > 1:
                    # Bütün elementləri təmizləyirik
                    self.clear_all_elements()
                    # Yeni elementləri yaradırıq
                    self.create_animation_elements()
                    self.create_loading_text()
                else:
                    self.loading_canvas.after(100, self.animate_elements)
                    return
            
            if self.canvas_width <= 1 or self.canvas_height <= 1:
                self.loading_canvas.after(100, self.animate_elements)
                return
            
            # Animasiya vaxtı
            self.animation_time += 0.04  # Daha sürətli
            
            # Mərkəz koordinatları
            center_x = self.canvas_width // 2
            center_y = self.canvas_height // 2
            
            # Responsive ölçülər
            min_size = min(self.canvas_width, self.canvas_height)
            base_radius = min_size // 8
            
            # Canvas-ı tam təmizləyirik
            self.loading_canvas.delete("all")
            self.create_white_background()
            
            # Rənglər
            colors = [
                '#FF6B9D', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFE66D',
                '#FF8A80', '#9575CD', '#4DB6AC', '#FFB74D', '#81C784',
                '#64B5F6', '#F06292', '#FFD54F', '#A1887F', '#90A4AE'
            ]
            
            # Elementləri yenidən çəkirik
            for element in self.elements:
                if element['type'] == 'circle':
                    # Spiral hərəkət
                    element['angle'] += element['speed']
                    
                    # Responsive radius hesablaması
                    responsive_radius = element['base_radius'] + (base_radius // 3) * math.sin(self.animation_time + element['phase'])
                    radius = responsive_radius
                    
                    x = center_x + radius * math.cos(element['angle'])
                    y = center_y + radius * math.sin(element['angle'])
                    
                    # Dinamik ölçü - böyüyüb-kiçilir
                    size_factor = 1 + 0.5 * math.sin(self.animation_time * 2 + element['phase'])
                    responsive_element_size = element['base_element_size'] * size_factor
                    dynamic_radius = responsive_element_size
                    
                    # Dinamik rəng dəyişməsi
                    color_index = int((self.animation_time * 10 + element['phase'] * 10)) % len(colors)
                    current_color = colors[color_index]
                    
                    # Glow effekti
                    glow_radius = dynamic_radius + 5
                    glow = self.loading_canvas.create_oval(
                        x-glow_radius, y-glow_radius,
                        x+glow_radius, y+glow_radius,
                        fill=current_color, outline='', stipple='gray25'
                    )
                    element['glow_id'] = glow
                    
                    # Əsas element - dolu və ya boş
                    if element['fill_type'] == 0:  # Dolu
                        circle = self.loading_canvas.create_oval(
                            x-dynamic_radius, y-dynamic_radius,
                            x+dynamic_radius, y+dynamic_radius,
                            fill=current_color, outline='white', width=2
                        )
                    else:  # Boş
                        circle = self.loading_canvas.create_oval(
                            x-dynamic_radius, y-dynamic_radius,
                            x+dynamic_radius, y+dynamic_radius,
                            fill='', outline=current_color, width=3
                        )
                    element['canvas_id'] = circle
                    
                    # Pulse effekti
                    if random.random() < 0.08:  # 8% ehtimal
                        self.create_pulse_effect(x, y, current_color)
                
                elif element['type'] == 'ring':
                    # Dönən halqa
                    element['angle'] += element['speed']
                    
                    # Responsive radius
                    responsive_radius = element['radius'] * (min_size / 400)
                    x = center_x + responsive_radius * math.cos(element['angle'])
                    y = center_y + responsive_radius * math.sin(element['angle'])
                    
                    # Dinamik ölçü
                    size_factor = 1 + 0.6 * math.sin(self.animation_time * 3 + element['phase'])
                    responsive_size = element['base_element_size'] * size_factor
                    dynamic_size = responsive_size
                    
                    # Dinamik rəng dəyişməsi
                    color_index = int((self.animation_time * 8 + element['phase'] * 8)) % len(colors)
                    current_color = colors[color_index]
                    
                    # Halqa çəkirik - dolu və ya boş
                    if element['fill_type'] == 0:  # Dolu
                        ring = self.loading_canvas.create_oval(
                            x-dynamic_size, y-dynamic_size,
                            x+dynamic_size, y+dynamic_size,
                            fill=current_color, outline='white', width=1
                        )
                    else:  # Boş
                        ring = self.loading_canvas.create_oval(
                            x-dynamic_size, y-dynamic_size,
                            x+dynamic_size, y+dynamic_size,
                            fill='', outline=current_color, width=4
                        )
                    element['canvas_id'] = ring
            
            # Loading mətni yenidən yaradırıq
            self.create_loading_text()
            
            # Hissəcikləri animasiya edirik
            self.animate_particles(current_time)
            
            # Növbəti frame
            self.loading_canvas.after(40, self.animate_elements)  # Daha sürətli
        except Exception as e:
            logging.warning(f"Loading animasiyası xətası: {e}")
            return

    def clear_all_elements(self):
        """Bütün elementləri təmizləyir."""
        # Bütün canvas elementlərini təmizləyirik
        self.loading_canvas.delete("all")
        # Ağ arxa fonu yenidən yaradırıq
        self.create_white_background()
        # Elementləri təmizləyirik
        self.elements.clear()
        self.particles.clear()

    def animate_particles(self, current_time):
        """Hissəcikləri animasiya edir."""
        for particle in self.particles[:]:
            # Responsive sürət yeniləməsi - pəncərə dəyişibsə
            if 'base_speed' in particle:
                current_min_size = min(self.canvas_width, self.canvas_height)
                current_base_speed = current_min_size / 200
                
                # Sürəti yeniləyirik
                speed_factor = current_base_speed / particle['base_speed']
                particle['vx'] *= speed_factor
                particle['vy'] *= speed_factor
                particle['base_speed'] = current_base_speed
            
            # Hissəciyi yeniləyirik
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= particle['decay']
            
            # 6 saniyə sonra və ya həyat bitibsə silirik
            if (particle['life'] <= 0 or 
                current_time - particle['created_time'] > 6.0):  # 6 saniyə
                self.particles.remove(particle)
                continue
            
            # Hissəciyi çəkirik
            size = particle['size'] * particle['life']
            color = particle['color']
            
            # Rəng hesablaması
            if color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                
                # Alpha effekti
                r = max(0, min(255, int(r * particle['life'])))
                g = max(0, min(255, int(g * particle['life'])))
                b = max(0, min(255, int(b * particle['life'])))
                
                particle_color = f'#{r:02x}{g:02x}{b:02x}'
                
                # Hissəciyi çəkirik
                self.loading_canvas.create_oval(
                    particle['x'] - size, particle['y'] - size,
                    particle['x'] + size, particle['y'] + size,
                    fill=particle_color, outline='', width=0
                )

    def hide(self):
        """Loading animasiyasını gizlədir."""
        print("🔵 DEBUG: LoadingAnimation.hide() başladı")
        self.animation_running = False
        if self.loading_frame:
            print("🔵 DEBUG: Loading frame destroy edilir")
            self.loading_frame.destroy()
            self.loading_frame = None
            self.loading_canvas = None
            print("🔵 DEBUG: Loading frame destroy edildi")
        print("🔵 DEBUG: LoadingAnimation.hide() tamamlandı") 
