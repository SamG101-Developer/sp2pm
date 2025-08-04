import socket
from threading import Thread

from PyQt6.QtCore import QObject, pyqtSignal


class Receiver(QObject):
    _port: int
    _socket: socket.socket
    _receiver_thread: Thread
    _send_to_socket: socket.socket

    data_received = pyqtSignal(bytes)

    def __init__(self, port: int) -> None:
        super().__init__()
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("", self._port))
        self._socket.listen(5)

        self._receiver_thread = Thread(target=self._accept_connection)
        self._receiver_thread.start()

    def _accept_connection(self) -> None:
        conn, addr = self._socket.accept()
        self._send_to_socket = conn
        self.receive_data(conn)

    def receive_data(self, conn: socket.socket) -> None:
        data = bytearray()
        chunk_size = pow(2, 24)
        while True:
            image = b""
            while not image.endswith(b"\n"):
                chunk = conn.recv(chunk_size)  # 64KB chunks
                if not chunk:
                    break
                image += chunk
            if not image:
                break
            self.data_received.emit(image)
