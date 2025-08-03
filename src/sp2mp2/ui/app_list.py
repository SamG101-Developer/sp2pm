import psutil
import win32con
import win32gui
import win32process
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QComboBox, QWidget


class AppList(QWidget):
    _app_selection: QComboBox
    _app_scan_timer: QTimer

    def __init__(self, parent: QWidget, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._app_selection = kwargs.get("app_selection")
        self._app_scan_timer = QTimer(self, singleShot=False, timeout=self._scan_apps)

    def begin_scanning(self, interval: int = 1000) -> None:
        self._app_scan_timer.start(interval)

    def _scan_apps(self) -> None:
        def _callback(hwnd, _) -> None:
            # Skip if the window is invisible.
            if not win32gui.IsWindowVisible(hwnd):
                return

            # Skip if the window has no title.
            if not win32gui.GetWindowText(hwnd):
                return

            # Skip if the window is a tool window (like task manager).
            if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
                return

            # Skip if the window has no size.
            rect = win32gui.GetWindowRect(hwnd)
            if rect[2] - rect[0] <= 0 or rect[3] - rect[1] <= 0:
                return

            # Get the window title and process ID.
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # Check if the PID is already in the selection box
            if any(self._app_selection.itemData(i, role=Qt.ItemDataRole.UserRole)[1] == pid for i in range(self._app_selection.count())):
                return

            try:
                # Ensure the combo box is enabled before adding items.
                self._app_selection.setEnabled(True)

                # Get the process information.
                process = psutil.Process(pid)
                exe = process.exe()
                name = process.name()

                # Add the information to the combo box.
                self._app_selection.addItem(name)
                self._app_selection.setItemData(self._app_selection.count() - 1, (hwnd, pid, name, title), role=Qt.ItemDataRole.UserRole)

            except psutil.NoSuchProcess:
                # If there is an error with the process, skip it.
                self._app_selection.setDisabled(True)

            except psutil.AccessDenied:
                # If access is denied, disable the selection box.
                self._app_selection.setDisabled(True)

        win32gui.EnumWindows(_callback, None)
