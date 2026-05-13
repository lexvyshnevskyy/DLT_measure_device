from __future__ import annotations

from typing import Optional

import serial


class RSConnector:
    START_BYTE = 0xAA

    def __init__(self, port: str = '/dev/ttyUSB0', speed: int = 9600):
        self.port = port
        self.speed = speed
        self.ser: Optional[serial.Serial] = None
        self._rx_buffer = bytearray()
        self.reconnect()

    def reconnect(self) -> bool:
        self.close()
        self._rx_buffer.clear()
        try:
            self.ser = serial.Serial(self.port, self.speed, timeout=0.05)
            return True
        except Exception:
            self.ser = None
            return False

    def is_open(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def close(self) -> None:
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    def sent_message(self, message=b''):
        if not self.is_open():
            return 0
        self.ser.reset_input_buffer()
        self._rx_buffer.clear()
        return self.ser.write(message)

    def read_message(self) -> bytes:
        if not self.is_open():
            return b''
        waiting = self.ser.in_waiting
        if waiting <= 0:
            return b''
        return self.ser.read(waiting)

    def read_complete_frame(self, expected_length: int = 22) -> Optional[bytes]:
        """Return one complete frame, or None if a complete frame is not available yet.

        The old implementation only accepted `in_waiting == expected_length`.
        That is fragile: normal serial timing can produce 0, partial, or multiple
        frames in the buffer. This implementation keeps a local buffer, searches
        for the 0xAA start byte, and returns exactly one complete frame.
        """
        if not self.is_open():
            return None

        waiting = self.ser.in_waiting
        if waiting > 0:
            self._rx_buffer.extend(self.ser.read(waiting))

        # Prevent unbounded growth if the stream is garbage or uses the wrong baud.
        if len(self._rx_buffer) > expected_length * 20:
            del self._rx_buffer[:-expected_length]

        # Synchronize to start byte.
        try:
            start_index = self._rx_buffer.index(self.START_BYTE)
        except ValueError:
            self._rx_buffer.clear()
            return None

        if start_index > 0:
            del self._rx_buffer[:start_index]

        if len(self._rx_buffer) < expected_length:
            return None

        frame = bytes(self._rx_buffer[:expected_length])
        del self._rx_buffer[:expected_length]
        return frame
