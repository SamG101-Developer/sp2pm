from __future__ import annotations

import functools
import json
import pickle
import socket
from typing import Optional

import psutil
import win32con
import win32gui
import win32process
from PyQt6.QtCore import QSize, QTimer, Qt, pyqtSlot
from PyQt6.QtGui import QImage, QKeyEvent, QKeySequence, QPixmap
from PyQt6.QtWidgets import QApplication, QComboBox, QDialog, QGroupBox, QHBoxLayout, QLabel, QLayoutItem, \
    QLineEdit, \
    QPushButton, \
    QScrollArea, \
    QTabWidget, QVBoxLayout, \
    QWidget

from sp2mp.broadcaster import Broadcaster, EventProtocol, KeyboardEvent
from sp2mp.receiver import Receiver
from sp2mp.screenshotter import ScreenShotter


class UI(QDialog):
    _app_scan_timer: QTimer

    _app_label: QLabel
    _app_preview: QLabel
    _client_addresses: QWidget
    _current_app_selection_data: Optional[tuple[int, int, str, str]]
    _key_mapping_profiles: QVBoxLayout
    _client_bind_port: QLineEdit

    _current_key_mapping_name: QLabel
    _current_key_mapping: dict[int, int]

    _broadcaster: Optional[Broadcaster]
    _receiver: Optional[Receiver]
    _receiver_widget: ReceiverWidget

    def __init__(self, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._app_scan_timer = QTimer(timeout=self._scan_apps, singleShot=False)
        self._current_key_mapping = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Server vs client tabs
        tabs = QTabWidget()
        tabs.addTab(server_tab := QWidget(), "Server")
        tabs.addTab(client_tab := QWidget(), "Client")

        # Application selection frame
        app_selection_frame = QGroupBox()
        app_selection_frame.setTitle("Applications")
        app_selection_frame.setLayout(QVBoxLayout())

        self._app_selection = QComboBox(self)
        self._app_selection.currentIndexChanged.connect(self._select_app)
        self._app_preview = QLabel(self)
        self._app_preview.setFixedSize(
            QApplication.primaryScreen().size().scaled(QSize(300, 300), Qt.AspectRatioMode.KeepAspectRatio))

        app_selection_frame.layout().addWidget(self._app_selection)
        app_selection_frame.layout().addWidget(self._app_preview)

        # Network settings frame
        network_settings_frame = QGroupBox()
        network_settings_frame.setTitle("Network Settings")
        network_settings_frame.setLayout(QVBoxLayout())

        self._client_addresses = QWidget()
        self._client_addresses.setLayout(QVBoxLayout())
        self._client_addresses.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self._client_addresses.layout().addWidget(
            QPushButton("+", clicked=lambda: self._generate_new_client_addresses_widget()))

        network_settings_frame.layout().addWidget(QLabel("Client Address:"))
        network_settings_frame.layout().addWidget(self._client_addresses)

        # Key mapping frame
        key_mapping_frame = QGroupBox()
        key_mapping_frame.setTitle("Key Mapping")
        key_mapping_frame.setLayout(QVBoxLayout())

        create_profile_button = QPushButton("Create New Profile")
        create_profile_button.clicked.connect(
            lambda _: self._open_new_keymapping_profile_dialog(self._current_app_selection_data[2]))

        self._key_mapping_profiles = QVBoxLayout()
        self._key_mapping_profiles.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._current_key_mapping_name = QLabel("Current Key Mapping: <span style='color: red; font-weight: bold;'>None</span>")
        key_mapping_frame.layout().addWidget(self._current_key_mapping_name)
        key_mapping_frame.layout().addWidget(create_profile_button)
        key_mapping_frame.layout().addLayout(self._key_mapping_profiles)

        # Client bind to port.
        client_bind_frame = QGroupBox()
        client_bind_frame.setTitle("Client Bind Port")
        client_bind_frame.setLayout(QVBoxLayout())
        client_bind_frame.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        self._client_bind_port = QLineEdit()
        self._client_bind_port.setInputMask("00000;_")
        self._client_bind_port.setText("20000")
        self._receiver_widget = ReceiverWidget()

        my_ip_label = QLabel(f"My IP Address: {socket.gethostbyname(socket.gethostname())}")
        confirm_bind_button = QPushButton("Bind", clicked=self._start_receiving)

        client_bind_frame.layout().addWidget(my_ip_label)
        client_bind_frame.layout().addWidget(self._client_bind_port)
        client_bind_frame.layout().addWidget(confirm_bind_button)

        # Server layout.
        server_tab.setLayout(server_layout := QVBoxLayout())
        server_layout.addWidget(app_selection_frame)
        server_layout.addWidget(network_settings_frame)
        server_layout.addWidget(key_mapping_frame)
        server_layout.addWidget(QPushButton("Broadcast", clicked=self._start_broadcasting))

        # Client layout.
        client_tab.setLayout(client_layout := QVBoxLayout())
        client_layout.addWidget(client_bind_frame)

        # Primary layout.
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(tabs)

        # Scan for applications.
        self._app_scan_timer.start(1000)

    def _start_broadcasting(self) -> None:
        self.sender().setDisabled(True)
        self._broadcaster = Broadcaster(self._current_app_selection_data[0], [], [])

        for client in self._client_addresses.layout().findChildren(QHBoxLayout):
            address = client.itemAt(0).widget().text()
            port = int(client.itemAt(1).widget().text())
            if not address or not port: continue

            self._broadcaster.add_new_client(address, port)

        self._broadcaster.broadcast()

    def _start_receiving(self) -> None:
        self._receiver = Receiver(int(self._client_bind_port.text()))
        self._receiver.data_received.connect(self._receiver_widget.show_image)
        self._receiver_widget.showMaximized()
        self._receiver_widget._receiver = self._receiver

    def _fix_mapping(self, mapping: dict[int, int]) -> dict[int, int]:
        # Convert keys to integers
        return {int(k): int(v) for k, v in mapping.items()}

    def _load_key_mappings(self, name: str) -> None:
        with open("./data/key_mappings.json", "r") as fo:
            key_maps = json.load(fo)

        while self._key_mapping_profiles.count() > 0:
            item = self._key_mapping_profiles.itemAt(0)
            self._key_mapping_profiles.removeItem(item)

        if name in key_maps.keys():
            profiles = key_maps[name]["profiles"]
            for profile_name, profile in profiles.items():
                # Create UI elements for each key mapping profile
                profile_info = QHBoxLayout()
                profile_info.addWidget(profile_label := QLabel(f"{profile_name}: "))
                profile_info.addWidget(modify_profile_button := QPushButton("Modify", clicked=functools.partial(
                    self._open_modify_keymapping_profile_dialog, name, profile_name)))
                profile_info.addWidget(select_profile_button := QPushButton("Select", clicked=functools.partial(
                    self._select_keymapping_profile, name, profile_name)))
                profile_info.addWidget(delete_profile_button := QPushButton("Delete", clicked=functools.partial(
                    self._delete_keymapping_profile, name, profile_name)))

                self._key_mapping_profiles.addLayout(profile_info)

    def _modify_keymapping_profile(self, name: str, profile: str, mapping: dict[int, int], *, reload: bool = False) -> None:
        # Load the key mappings from the JSON file.
        with open("./data/key_mappings.json", "r") as fo:
            key_maps = json.load(fo)

        # Update the profile with the new mapping.
        if name not in key_maps:
            key_maps[name] = {"profiles": {}}

        # Check if the profile already exists
        existing_profile = key_maps[name]["profiles"].get(profile, None)
        if existing_profile:
            existing_profile["mapping"] = mapping
        else:
            key_maps[name]["profiles"][profile] = {
                "name": profile,
                "mapping": mapping}

        # Re-write the file with the updated key mappings.
        with open("./data/key_mappings.json", "w") as fo:
            json.dump(key_maps, fo, indent=4)

        if reload:
            self._load_key_mappings(name)

    def _select_keymapping_profile(self, name: str, profile: str) -> None:
        with open("./data/key_mappings.json", "r") as fo:
            key_maps = json.load(fo)
            mapping = self._fix_mapping(key_maps[name]["profiles"][profile]["mapping"])

        # Set the current key mapping to the selected profile.
        self._current_key_mapping_name.setText(f"Current Key Mapping: <span style='color: green; font-weight: bold;'>{profile}</span>")
        self._current_key_mapping = mapping

    def _delete_keymapping_profile(self, name: str, profile: str) -> None:
        # Load the key mappings from the JSON file.
        with open("./data/key_mappings.json", "r") as fo:
            key_maps = json.load(fo)

        # Remove the profile from the key mappings and re-write the file.
        key_maps[name].remove(profile)
        with open("./data/key_mappings.json", "w") as fo:
            json.dump(key_maps, fo, indent=4)

    def _serialize_keymapping_profile(self, name: str, profile: str, layout: QVBoxLayout, *, reload: bool = False) -> None:
        mappings = {}
        for mapping in layout.findChildren(QHBoxLayout):
            old_key = mapping.property("old_key")
            new_key = mapping.property("new_key")
            if old_key._has_selection and new_key._has_selection:
                mappings[old_key._captured_key_code] = new_key._captured_key_code

        self._modify_keymapping_profile(name, profile, mappings, reload=reload)

    def _open_modify_keymapping_profile_dialog(self, name: str, profile: str) -> None:

        with open("./data/key_mappings.json", "r") as fo:
            key_maps = json.load(fo)
            mapping = self._fix_mapping(key_maps[name]["profiles"][profile]["mapping"])

        dialog = QDialog(self)
        dialog.setLayout(QVBoxLayout())
        dialog.layout().addWidget(scroller := QScrollArea())
        dialog.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        scroller.setWidgetResizable(True)
        scroller.setWidget(content := QWidget())
        content.setLayout(QVBoxLayout())
        dialog.layout().addWidget(
            QPushButton("+", clicked=lambda: self._generate_new_key_mapping_widget(content.layout())))

        for k, v in mapping.items():
            mapping = self._generate_new_key_mapping_widget(content.layout(), pre_checked=True)
            mapping.property("old_key").setText(QKeySequence(k).toString(QKeySequence.SequenceFormat.NativeText).lower())
            mapping.property("new_key").setText(QKeySequence(v).toString(QKeySequence.SequenceFormat.NativeText).lower())
            mapping.property("old_key")._captured_key_code = k
            mapping.property("new_key")._captured_key_code = v

        # Confirm and cancel buttons
        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(lambda _: self._serialize_keymapping_profile(name, profile, content.layout()))
        confirm_button.clicked.connect(dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)

        dialog.layout().addLayout(button_layout)
        dialog.exec()

    @pyqtSlot(str)
    def _open_new_keymapping_profile_dialog(self, name: str) -> None:
        dialog = QDialog(self)
        dialog.setLayout(QVBoxLayout())
        dialog.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        dialog.layout().addWidget(profile_name := QLineEdit())
        dialog.layout().addWidget(
            QPushButton("+", clicked=lambda: self._generate_new_key_mapping_widget(content.layout())))
        dialog.layout().addWidget(scroller := QScrollArea())
        profile_name.setPlaceholderText("Profile Name")

        scroller.setWidgetResizable(True)
        scroller.setWidget(content := QWidget())
        content.setLayout(QVBoxLayout())

        # Confirm and cancel buttons
        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(
            lambda: self._serialize_keymapping_profile(name, profile_name.text(), content.layout(), reload=True))
        confirm_button.clicked.connect(dialog.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        dialog.layout().addLayout(button_layout)
        dialog.exec()

    def _generate_new_key_mapping_widget(self, owner_layout: QVBoxLayout, *, pre_checked: bool = False) -> QHBoxLayout:
        key_mapping = QHBoxLayout()

        remove_key_mapping_button = QPushButton("-")
        remove_key_mapping_button.setFixedSize(QSize(32, 32))

        key_mapping.addWidget(old := KeyCaptureButton())
        key_mapping.addWidget(QLabel("->"))
        key_mapping.addWidget(new := KeyCaptureButton())
        key_mapping.addWidget(remove_key_mapping_button)

        key_mapping.setProperty("old_key", old)
        key_mapping.setProperty("new_key", new)

        if pre_checked:
            old._has_selection = True
            new._has_selection = True

        owner_layout.addLayout(key_mapping)
        remove_key_mapping_button.clicked.connect(functools.partial(
            self._remove_key_mapping, owner_layout.itemAt(owner_layout.count() - 1), owner_layout))
        return key_mapping

    def _remove_key_mapping(self, key_mapping: QLayoutItem, owner_layout: QVBoxLayout) -> None:
        owner_layout.removeItem(key_mapping)
        key_mapping.layout().deleteLater()

    def _generate_new_client_addresses_widget(self) -> QHBoxLayout:
        client_address = QLineEdit()
        # client_address.setInputMask("000.000.000.000;_")
        client_address.setText("127.0.0.1")

        client_port = QLineEdit()
        client_port.setInputMask("00000;_")
        client_port.setText("20000")

        client_info = QHBoxLayout()
        client_info.addWidget(client_address)
        client_info.addWidget(client_port)

        remove_client_button = QPushButton("-")
        remove_client_button.setFixedSize(QSize(32, 32))
        client_info.addWidget(remove_client_button)

        self._client_addresses.layout().addLayout(client_info)
        remove_client_button.clicked.connect(functools.partial(
            self._remove_client, self._client_addresses.layout().itemAt(self._client_addresses.layout().count() - 1)))
        return client_info

    def _remove_client(self, client_info: QLayoutItem) -> None:
        self._client_addresses.layout().removeItem(client_info)
        client_info.layout().deleteLater()

    def _scan_apps(self) -> None:
        def _callback(hwnd, _) -> None:
            if not win32gui.IsWindowVisible(hwnd):
                return
            if not win32gui.GetWindowText(hwnd):
                return
            if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
                return

            rect = win32gui.GetWindowRect(hwnd)
            if rect[2] - rect[0] <= 0 or rect[3] - rect[1] <= 0:
                return

            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # Check if the PID is already in the selection box
            if any(self._app_selection.itemData(i, role=Qt.ItemDataRole.UserRole)[1] == pid for i in
                   range(self._app_selection.count())):
                return

            try:
                self._app_selection.setEnabled(True)

                process = psutil.Process(pid)
                exe = process.exe()
                name = process.name()

                self._app_selection.addItem(name)
                self._app_selection.setItemData(
                    self._app_selection.count() - 1,
                    (hwnd, pid, name, title),
                    role=Qt.ItemDataRole.UserRole)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self._app_selection.setDisabled(True)

        win32gui.EnumWindows(_callback, None)

    @pyqtSlot(int)
    def _select_app(self, x: int) -> None:
        if data := self._app_selection.itemData(x, role=Qt.ItemDataRole.UserRole):
            hwnd, pid, name, title = self._app_selection.itemData(x, role=Qt.ItemDataRole.UserRole)
            self._current_app_selection_data = hwnd, pid, name, title
            screen_shot = ScreenShotter.take_screenshot(hwnd)
            self._app_preview.setPixmap(
                QPixmap.fromImage(screen_shot.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio)))

            self._load_key_mappings(name)


class KeyCaptureButton(QPushButton):
    _capture_next_key: bool
    _has_selection: bool
    _captured_key_code: Optional[int]

    def __init__(self, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.setFixedSize(QSize(32, 32))
        self._capture_next_key = False
        self._has_selection = False
        self._captured_key_code = None

        self.clicked.connect(self._capture_key)
        self.setText("N/A")

    def _capture_key(self) -> None:
        self.setText("...")
        self._capture_next_key = True
        self._has_selection = False

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._capture_next_key:
            self._captured_key_code = event.key()
            self.setText(event.text())
            self._capture_next_key = False
            self._has_selection = True
            event.accept()
        else:
            super().keyPressEvent(event)


class ReceiverWidget(QWidget):
    _image_display: QLabel
    _receiver: Optional[Receiver]

    def __init__(self, parent: Optional[QWidget] = None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._receiver = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self._image_display = QLabel(self)
        self._image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_display.setText("Loading...")

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._image_display)
        self.hide()

    @pyqtSlot(bytes)
    def show_image(self, image_data: bytes) -> None:
        image = QImage.fromData(image_data)
        self._image_display.setPixmap(QPixmap.fromImage(image))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Capture key press events and forward them to the server.
        key = event.nativeVirtualKey()
        mapped_event = KeyboardEvent(key_code=key, key_down=True)
        self._receiver._send_to_socket.send(EventProtocol.KEYBOARD.value + pickle.dumps(mapped_event))
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return

        # Capture key release events and forward them to the server.
        key = event.nativeVirtualKey()
        mapped_event = KeyboardEvent(key_code=key, key_down=False)
        self._receiver._send_to_socket.send(EventProtocol.KEYBOARD.value + pickle.dumps(mapped_event))
        super().keyReleaseEvent(event)
