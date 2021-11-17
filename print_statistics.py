#!/usr/bin/env python3

from serial import Serial
import argparse
import struct
import time

GET_DEV_INFO = b'a'
GET_STATISTICS = b'b'

SERIAL_BAUD_RATE = 115200
SERIAL_TIMEOUT = 0.5

def spin_fetch(port, request, size):
    sn = None
    while sn != request:
        port.write(request)
        sn = port.read()

    if size > 1:
        return sn + port.read(size - 1)
    return sn

class OptvController:
    def __init__(self):
        self._inst = None
        self._sn = None

    @property
    def serial_number(self):
        """returns serial number from latest connect or None"""
        return self._sn

    def connect(self, port):
        """connect to device at serial port"""
        if self._inst is None:
            self._inst = Serial(port, SERIAL_BAUD_RATE, timeout=SERIAL_TIMEOUT)

        # load constants into local vars
        sn = spin_fetch(self._inst, GET_DEV_INFO, 10)
        self._sn = struct.unpack('<LL', sn[1:-1])[0]

    def disconnect(self):
        """disconnect from device"""
        if self._inst is not None:
            self._inst.close()

    def get_statistics(self):
        """
        returns a tuple containing stats
        """
        code = spin_fetch(self._inst, GET_STATISTICS, 1)

        num_inputs = struct.unpack('<B', self._inst.read())[0]

        input_voltages = struct.unpack(
            '<' + 'L' * num_inputs,
            self._inst.read(num_inputs * 4) # 4 bytes in 32 bits
        )

        input_currents = struct.unpack(
            '<' + 'L' * num_inputs,
            self._inst.read(num_inputs * 4) # 4 bytes in 32 bits
        )

        (output_volt, load_current, batt_curr) = struct.unpack(
            '<LLL',
            self._inst.read(12) # 4 bytes in 32 bits
        )

        self._inst.read() # clear the ;

        return (
            input_voltages,
            input_currents,
            output_volt,
            load_current,
            batt_curr,
        )

    def __del__(self):
        self.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prints telemetry data in a loop')
    parser.add_argument('--device', '-d', type=str, help='path to serial device file')
    args = parser.parse_args()

    solar_panel = OptvController()
    solar_panel.connect(args.device)

    print("serial number: ", solar_panel.serial_number)

    try:
        while True:
            print(solar_panel.get_statistics())
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    solar_panel.disconnect()
