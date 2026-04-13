from __future__ import annotations

from typing import Optional

import serial


class RSConnector:
    def __init__(self, port: str = '/dev/ttyUSB0', speed: int = 9600):
        self.port = port
        self.speed = speed
        self.ser: Optional[serial.Serial] = None
        self.reconnect()

    def reconnect(self) -> bool:
        self.close()
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
        return self.ser.write(message)

    def read_message(self) -> bytes:
        if not self.is_open():
            return b''
        result = self.ser.read(self.ser.in_waiting)
        self.ser.reset_input_buffer()
        return result

    def read_complete_frame(self, expected_length: int = 22) -> Optional[bytes]:
        if not self.is_open():
            return None

        waiting = self.ser.in_waiting
        if waiting == expected_length:
            return self.read_message()
        if waiting > expected_length:
            self.ser.reset_input_buffer()
        return None
