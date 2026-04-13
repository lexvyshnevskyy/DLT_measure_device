import time

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
    """Parser for binary data frames from the E7-20 device."""

    SecParam = [
        'Cp', 'Lp', 'Rp', 'Gp', 'Bp', '|Y|', 'Q', 'Cs', 'Ls', 'Rs', 'Phi', 'Xs', '|Z|', 'D', 'I'
    ]
    imparam = SecParam
    limit = [
        '10 M Om', '1 M Om', '100 k Om', '10 k Om', '1 k Om', '100 Om', '10 Om', '1 Om'
    ]

    def __init__(self):
        self.__new_instance = False
        self.__end_of_input = False
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

    def parse_data(self, line: bytes):
        if self.__new_instance and self.__end_of_input:
            self.__init__()

        if b'\xaa' in line:
            self.__new_instance = True

        if not self.__new_instance or len(line) < 21:
            return

        limit_index = self.decode_value(line[9:10]) - 1
        im_param_index = self.decode_value(line[10:11])
        sec_param_index = self.decode_value(line[11:12])

        self.parsedData = {
            'OffSet': f'{self.decode_value(line[1:3]) / 100:.2f}',
            'Level': f'{self.decode_value(line[3:4]) / 100:.2f}',
            'Freq': self.decode_value(line[4:6]),
            'Freq10': self.decode_value(line[6:7]),
            'Frequency': self.__calculate('Frequency', self.decode_value(line[4:6]), self.decode_value(line[6:7])),
            'Limit': self.limit[limit_index] if 0 <= limit_index < len(self.limit) else '',
            'ImParam': self.imparam[im_param_index] if 0 <= im_param_index < len(self.imparam) else '',
            'SecParam': self.SecParam[sec_param_index] if 0 <= sec_param_index < len(self.SecParam) else '',
            'SecValue': self.decode_value(line[12:15]),
            'SecValue10': self.__calculate('SecValue10', self.decode_value(line[15:16], True)),
            'SecondValue': self.__calculate(
                'SecondValue',
                self.decode_value(line[12:15]),
                self.__calculate('SecValue10', self.decode_value(line[15:16], True)),
            ),
            'ImValue': self.decode_value(line[16:19]),
            'ImValue10': self.decode_value(line[19:20], True),
            'FirstValue': self.__calculate(
                'FirstValue',
                self.decode_value(line[16:19]),
                self.decode_value(line[19:20], True),
            ),
            'OnChange': self.decode_value(line[20:21]),
            'TimeStamp': f'{time.time():.0f}',
        }
        self.__end_of_input = True
        self.__data_ready = True

    def decode_value(self, line: bytes, use_265: bool = False) -> int:
        temp = int.from_bytes(line, byteorder='little')
        if use_265:
            return temp - 0x100 if line[len(line) - 1] > 128 else temp
        return temp - 0xFFFF if line[len(line) - 1] > 128 else temp

    def __calculate(self, param: str = '', def_param: int = 0, base_param: int = 0):
        if param == 'Frequency':
            return def_param * pow(10, base_param if base_param >= 0 else 1)
        if param == 'SecValue10':
            return def_param - 0x100 if def_param > 0x80 else def_param
        if param == 'SecondValue':
            return f'{(0 if def_param > 0x186A0 else def_param * pow(10, base_param)):.5f}'
        if param == 'FirstValue':
            return f'{(def_param * pow(10, base_param)):.5f}'
        return 0
