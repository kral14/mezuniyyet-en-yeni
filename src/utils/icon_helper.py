import os
import sys
import tkinter as tk


def resolve_icon_path() -> str:
    """Return absolute path to the app icon (.ico), compatible with frozen and dev modes."""
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller EXE mode - icons are in root icons folder
            base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
            candidate = os.path.join(base_path, 'icons', 'icon.ico')
            if os.path.exists(candidate):
                return candidate
        # Dev mode: src/icons-dan icon yüklə
        src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        candidate = os.path.join(src_dir, 'icons', 'icon.ico')
        if os.path.exists(candidate):
            return candidate
    except Exception:
        pass
    return ''


def apply_window_icon(window: tk.Misc) -> None:
    """Apply the app icon to a Tk/Toplevel window if available."""
    try:
        icon_path = resolve_icon_path()
        if icon_path and os.path.exists(icon_path):
            # Prefer iconbitmap for .ico files on Windows
            if hasattr(window, 'iconbitmap'):
                window.iconbitmap(icon_path)
            elif hasattr(window, 'iconphoto'):
                try:
                    from PIL import Image, ImageTk  # optional
                    img = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(img)
                    window.iconphoto(True, photo)
                except Exception:
                    pass
    except Exception:
        # Never raise from icon application
        pass


_hook_installed = False


def install_global_toplevel_icon() -> None:
    """Monkey-patch tk.Toplevel to always apply app icon after construction.

    Safe to call multiple times; only first call installs the hook.
    """
    global _hook_installed
    if _hook_installed:
        return
    _hook_installed = True

    original_init = tk.Toplevel.__init__

    def _wrapped_init(self, *args, **kwargs):  # type: ignore[no-redef]
        original_init(self, *args, **kwargs)
        apply_window_icon(self)

    tk.Toplevel.__init__ = _wrapped_init  # type: ignore[assignment]


