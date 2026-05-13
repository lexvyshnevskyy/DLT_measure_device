import time
from typing import Optional


menu = {
    'Menu': b'\x00',
    'Right': b'\x01',
    'Z': b'\x02',
    'R': b'\x03',
    'Down': b'\x04',
    'Enter': b'\x05',
    'Up': b'\x06',
    'L': b'\x07',
    '0': b'\x08',
    'Left': b'\x09',
    'I': b'\x0a',
    'C': b'\x0b',
    'Offset': b'\x0c',
    'Freq': b'\x0d',
    'Level': b'\x0e',
    'Mode': b'\x0f',
}


class ParseData:
    """Parser for 22-byte binary frames from the E7-20 device."""

    FRAME_LENGTH = 22
    START_BYTE = 0xAA

    SecParam = [
        'Cp', 'Lp', 'Rp', 'Gp', 'Bp', '|Y|', 'Q', 'Cs', 'Ls', 'Rs', 'Phi', 'Xs', '|Z|', 'D', 'I'
    ]
    imparam = SecParam
    limit = [
        '10 M Om', '1 M Om', '100 k Om', '10 k Om', '1 k Om', '100 Om', '10 Om', '1 Om'
    ]

    def __init__(self):
        self.__data_ready = None
        self.parsedData = {
            'OffSet': None,
            'Level': None,
            'Freq': None,
            'Freq10': None,
            'Frequency': None,
            'Limit': None,
            'ImParam': None,
            'SecParam': None,
            'SecValue': None,
            'SecValue10': None,
            'SecondValue': None,
            'ImValue': None,
            'ImValue10': None,
            'FirstValue': None,
            'OnChange': None,
            'TimeStamp': None,
        }

    def dataReady(self):
        if self.__data_ready is not None:
            temp, self.__data_ready = self.parsedData, None
            return temp
        return None

    @staticmethod
    def decode_u(line: bytes) -> int:
        """Decode an unsigned little-endian integer."""
        if not line:
            return 0
        return int.from_bytes(line, byteorder='little', signed=False)

    @staticmethod
    def decode_i8(line: bytes) -> int:
        """Decode one signed int8 exponent byte."""
        if not line:
            return 0
        value = int(line[0])
        return value - 0x100 if value >= 0x80 else value

    @staticmethod
    def _pow10(exponent: int) -> float:
        return float(pow(10, exponent))

    def parse_data(self, line: bytes) -> None:
        if len(line) < self.FRAME_LENGTH:
            return
        if line[0] != self.START_BYTE:
            return

        limit_index = self.decode_u(line[9:10]) - 1
        im_param_index = self.decode_u(line[10:11])
        sec_param_index = self.decode_u(line[11:12])

        freq = self.decode_u(line[4:6])
        freq10 = self.decode_i8(line[6:7])

        sec_value = self.decode_u(line[12:15])
        sec_value10 = self.decode_i8(line[15:16])

        im_value = self.decode_u(line[16:19])
        im_value10 = self.decode_i8(line[19:20])

        self.parsedData = {
            # Unsigned fields.
            'OffSet': self.decode_u(line[1:3]) / 100.0,
            'Level': self.decode_u(line[3:4]) / 100.0,
            'Freq': freq,
            'Freq10': freq10,
            'Frequency': freq * self._pow10(freq10),
            'Limit': self.limit[limit_index] if 0 <= limit_index < len(self.limit) else '',
            'ImParam': self.imparam[im_param_index] if 0 <= im_param_index < len(self.imparam) else '',
            'SecParam': self.SecParam[sec_param_index] if 0 <= sec_param_index < len(self.SecParam) else '',
            'SecValue': sec_value,
            'SecValue10': sec_value10,
            'SecondValue': 0.0 if sec_value > 0x186A0 else sec_value * self._pow10(sec_value10),
            'ImValue': im_value,
            'ImValue10': im_value10,
            'FirstValue': im_value * self._pow10(im_value10),
            # OnChange is a byte/status/counter field; do not sign-extend it.
            'OnChange': self.decode_u(line[20:21]),
            'TimeStamp': float(f'{time.time():.0f}'),
        }
        self.__data_ready = True

    # Backward-compatible helper name for older code/tests.
    def decode_value(self, line: bytes, use_265: bool = False) -> int:
        if use_265:
            return self.decode_i8(line[:1])
        return self.decode_u(line)
