import ctypes

import win32con
import win32gui
import win32ui
from PyQt6.QtGui import QImage

PW_RENDERFULLCONTENT = 0x00000002

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi


class ScreenShotter:
    @staticmethod
    def take_screenshot_OLD(hwnd: int) -> QImage:
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w, h = r - l, b - t

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        src_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = src_dc.CreateCompatibleDC()

        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(src_dc, w, h)
        save_dc.SelectObject(save_bitmap)
        save_dc.BitBlt((0, 0), (w, h), src_dc, (0, 0), win32con.SRCCOPY)

        int_array = save_bitmap.GetBitmapBits(True)
        image = QImage(int_array, w, h, QImage.Format.Format_ARGB32)

        src_dc.DeleteDC()
        save_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        win32gui.DeleteObject(save_bitmap.GetHandle())
        return image

    @staticmethod
    def take_screenshot(hwnd: int) -> QImage:
        # Get window rect
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w, h = r - l, b - t

        # Create device contexts
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        src_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = src_dc.CreateCompatibleDC()
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(src_dc, w, h)
        save_dc.SelectObject(save_bitmap)

        # Try PrintWindow first
        success = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)

        if not success:
            # Fallback: BitBlt from screen (works for layered/GPU apps)
            save_dc.BitBlt((0, 0), (w, h), src_dc, (0, 0), win32con.SRCCOPY)

        # Convert to QImage
        int_array = save_bitmap.GetBitmapBits(True)
        image = QImage(int_array, w, h, QImage.Format.Format_ARGB32)

        # Cleanup
        src_dc.DeleteDC()
        save_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        win32gui.DeleteObject(save_bitmap.GetHandle())
        return image
