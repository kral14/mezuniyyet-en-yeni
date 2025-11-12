import tkinter as tk
from tkinter import ttk
import time
import threading

# Loading animasiyasını import edirik
from ui.loading_animation import LoadingWindow

def test_loading():
    """Loading animasiyasını test edir"""
    print("Loading animasiyası başladılır...")
    
    # Loading pəncərəsini yaradırıq
    loading_window = LoadingWindow(root, "bounce")
    
    # Loading-i başladırıq
    loading_window.start_loading("Test animasiyası...")
    
    print("Loading pəncərəsi açıldı!")
    
    # 5 saniyə gözləyirik
    def close_after_5_seconds():
        time.sleep(5)
        print("5 saniyə keçdi, loading bağlanır...")
        root.after(0, loading_window.stop_loading)
    
    threading.Thread(target=close_after_5_seconds, daemon=True).start()

# Ana pəncərə
root = tk.Tk()
root.title("Loading Test")
root.geometry("400x300")

# Test düyməsi
test_button = ttk.Button(root, text="Loading Animasiyasını Test Et", command=test_loading)
test_button.pack(expand=True)

print("Test proqramı hazırdır!")
print("Düyməyə basın və loading animasiyasını görün...")

root.mainloop() 