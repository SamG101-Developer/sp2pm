from typing import Optional

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QKeyEvent, QKeySequence
from PyQt6.QtWidgets import QPushButton, QWidget


class KeyCaptureButton(QPushButton):
    _capture_next_key: bool
    _captured_key_code: Optional[int]
    _has_selection: bool

    def __init__(self, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.setFixedSize(QSize(32, 32))

        # No current key captured.
        self._capture_next_key = False
        self._has_selection = False
        self._captured_key_code = None

        # Connect the button click to the key capture method.
        self.clicked.connect(self._capture_key)
        self.setText("N/A")

    def _capture_key(self) -> None:
        # Reset the button to capture a new key.
        self.setText("...")
        self._capture_next_key = True
        self._has_selection = False

    def set_captured_key_code(self, key_code: int) -> None:
        # Manually set the captured key code and update the button text.
        self._captured_key_code = key_code
        self.setText(QKeySequence(key_code).toString())
        self._capture_next_key = False
        self._has_selection = True

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._capture_next_key:
            # Capture the key code and update the button text.
            self._captured_key_code = event.key()
            self.setText(event.text())

            # Reset the capture state (don't capture next key).
            self._capture_next_key = False
            self._has_selection = True
            event.accept()
        else:
            super().keyPressEvent(event)
