import time
from dataclasses import dataclass, field
from queue import Queue
from socket import socket
from threading import Thread

from PyQt6.QtCore import QBuffer

from sp2mp.screenshotter import ScreenShotter


@dataclass
class Client:
    host: str
    port: int
    queue: Queue = field(default_factory=Queue)
    thread: Thread = field(init=False)
    socket: socket = field(init=False)


class Broadcaster:
    _hwnd: int
    _clients: list[Client]
    _screenshot_thread: Thread

    def __init__(self, hwnd: int, hosts: list[str], ports: list[int]) -> None:
        self._hwnd = hwnd
        self._clients = [Client(host, port) for host, port in zip(hosts, ports)]

    def add_new_client(self, host: str, port: int, auto_broadcast: bool = False) -> None:
        client = Client(host, port)
        self._clients.append(client)
        if auto_broadcast:
            self._begin_client_thread(client)

    def _begin_client_thread(self, client: Client) -> None:
        thread = Thread(target=self._send_screenshots, args=(client,))
        thread.daemon = True
        thread.start()
        client.thread = thread

    def broadcast(self, fps: int = 60) -> None:
        self._screenshot_thread = Thread(target=self._screenshot_loop, args=(fps,))
        self._screenshot_thread.daemon = True
        self._screenshot_thread.start()

        for client in self._clients:
            self._begin_client_thread(client)

    def _screenshot_loop(self, fps: int) -> None:
        while True:
            # Todo: thread this logic (less time consuming per loop)?
            screenshot = ScreenShotter.take_screenshot(self._hwnd)
            for client in self._clients:
                client.queue.put(screenshot)

            # Sleep to maintain the desired FPS
            time.sleep(1 / fps)

    def _send_screenshots(self, client: Client) -> None:
        client.socket = socket()
        client.socket.connect((client.host, client.port))

        while True:
            screenshot = client.queue.get()
            if screenshot is None:
                break

            # Serialize the screenshot and send it over the socket.
            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.WriteOnly)
            screenshot.save(buffer, "JPG")
            data = buffer.data() + b"\n"  # Append newline to indicate end of image data
            client.socket.sendall(data.data())

            # Close the buffer after sending, and mark the task as done.
            buffer.close()
            client.queue.task_done()
