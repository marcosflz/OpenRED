"""Serial transport abstraction for the Test Bed module.

The real implementation wraps pyserial (115200 8N1, 1 s timeout). The mock
implementation is scripted and used by CI/tests (R6 of the migration plan).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable
from typing import Protocol


class Transport(Protocol):
    @property
    def connected(self) -> bool: ...

    def open(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None: ...

    def close(self) -> None: ...

    def write_line(self, command: str) -> None:
        """Send a command terminated by newline (ESP32 protocol)."""

    def read_line(self) -> str | None:
        """Block up to the configured timeout and return one line (without CR/LF), or None."""


class SerialTransport:
    def __init__(self) -> None:
        self._serial = None

    @property
    def connected(self) -> bool:
        return self._serial is not None and bool(getattr(self._serial, "is_open", False))

    def open(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        import serial  # imported lazily so the engine works without hardware libs

        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        time.sleep(2.0)  # ESP32 reset on DTR toggle settles before commands are sent
        self._serial.reset_input_buffer()

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            finally:
                self._serial = None

    def write_line(self, command: str) -> None:
        if self._serial is None:
            raise RuntimeError("serial port is not open")
        self._serial.write((command + "\n").encode("utf-8", errors="replace"))
        self._serial.flush()

    def read_line(self) -> str | None:
        if self._serial is None:
            return None
        raw = self._serial.readline()
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace").strip()


class MockTransport:
    """Scripted transport for tests: replies are queued and delivered in order.

    `script` is a list of lines. Each `write_line` may embed a `{"command": [...lines]}`.
    """

    def __init__(self, script: Iterable[str] | None = None) -> None:
        self._lock = threading.Lock()
        self.script: list[str] = [str(line) for line in (script or [])]
        self._inbox: list[str] = list(self.script)
        self._outbox: list[str] = []
        self._connected = False
        self._responses: dict[str, list[str]] = {}

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def sent(self) -> list[str]:
        return list(self._outbox)

    def respond_to(self, command: str, lines: Iterable[str]) -> None:
        with self._lock:
            self._responses[command] = list(lines)

    def push(self, lines: Iterable[str]) -> None:
        with self._lock:
            self._inbox.extend(lines)

    def open(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def write_line(self, command: str) -> None:
        if not self._connected:
            raise RuntimeError("mock transport is not open")
        with self._lock:
            self._outbox.append(command)
            self._inbox.extend(self._responses.get(command, []))

    def read_line(self) -> str | None:
        with self._lock:
            if self._inbox:
                return self._inbox.pop(0)
        return None


def list_ports() -> list[dict[str, str]]:
    try:
        from serial.tools import list_ports as _list_ports
        from serial.tools.list_ports_common import ListPortInfo
    except ImportError:  # pragma: no cover - pyserial is a core dependency
        return []
    ports: list[dict[str, str]] = []
    for port in _list_ports.comports():
        assert isinstance(port, ListPortInfo)
        ports.append({"device": port.device, "description": port.description or ""})
    return ports


class SerialMonitor:
    """Reads lines in a background thread and forwards them to a callback."""

    def __init__(self, transport: Transport, on_line: Callable[[str], None], interval: float = 0.05):
        self._transport = transport
        self._on_line = on_line
        self._interval = interval
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                line = self._transport.read_line()
            except Exception:  # serial read errors end the monitor, the UI shows disconnected
                break
            if line:
                self._on_line(line)
            else:
                time.sleep(self._interval)
