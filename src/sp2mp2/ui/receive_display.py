from typing import Optional

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ReceiverWidget(QWidget):
    _image_display: QLabel

    def __init__(self, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Create a QLabel to display the received image.
        self._image_display = QLabel(self)
        self._image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_display.setText("Loading...")

        # Add the QLabel to the layout of the widget.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._image_display)
        self.hide()

    @pyqtSlot(bytes)
    def show_image(self, image_data: bytes) -> None:
        # Convert the received bytes to a QImage and display it in the QLabel.
        image = QImage.fromData(image_data)
        self._image_display.setPixmap(QPixmap.fromImage(image))
