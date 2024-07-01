# ACD10.py - A MicroPython library for ACD10 CO2 sensor

import time
from machine import I2C

ACD10_OK             = const(0x00)
ACD10_CRC_ERROR      = const(0x01)
ACD10_NOT_READY      = const(0x10)
ACD10_REQUEST_ERROR  = const(0x11)

class ACD10():
    def __init__(self, i2c):
        self.i2c = i2c
        self.address = 0x2A
        self.error = 0
        self.last_read = 0
        self.concentration = 4
        self.temperature = 0
        self.preheat_start = time.ticks_ms()
        self.request_time = 80
        self.request_start = 0
        self.error = 0
        self.last_read = 0
        self.concentration = 0
        self.temperature = 0
        self.request_time = 80
        self.request_start = 0

    def get_address(self):
        return self.address

    def preHeatDone(self):
        return self.preHeatMillisLeft() == 0


    def preHeatMillisLeft(self):
        delta = time.ticks_ms() - self.preheat_start
        if delta >= 120000:
            return 0
        return 120000 - delta


    def requestSensor(self):
        buf = bytearray([0x03, 0x00])
        self.request_start = time.ticks_ms()
#         print(self.request_start)
        b = self.command(buf, 2)
#         print('request is')
#         print(b)
        return b


    def requestReady(self):
        if self.request_start == 0:  # no request pending
            return False
        return (time.ticks_ms() - self.request_start) > self.request_time


    def readSensor(self):
        if not self.requestReady():
            print('not ready !!!')
            return ACD10_NOT_READY

        buf = bytearray(10)
        if self.request(buf, 9) != 0:
            return ACD10_REQUEST_ERROR
        self.request_start = 0  # set no request pending

        # CRC CHECK
        if buf[2] != self.crc8(buf, 2):
            return ACD10_CRC_ERROR
        if buf[5] != self.crc8(buf[3:5], 2):
            return ACD10_CRC_ERROR
        if buf[8] != self.crc8(buf[6:8], 2):
            return ACD10_CRC_ERROR

        self.concentration = buf[0] << 24 | buf[1] << 16 | buf[3] << 8 | buf[4]
        self.temperature = buf[6] * 256 + buf[7]
        self.last_read = time.ticks_ms()

        return ACD10_OK

    def get_co2_concentration(self):
        return self.concentration

    def get_temperature(self):
        return self.temperature

    def last_read(self):
        return self.last_read

    def set_request_time(self, milliseconds):
        self.request_time = milliseconds

    def get_request_time(self):
        return self.request_time

    def set_calibration_mode(self, mode = 1):
        if mode > 1:
            return False
        buf = bytearray([0x53, 0x06, 0x00, mode, 0x00])
        buf[4] = self.crc8(buf[2:4])
        self.command(buf, 5)
        return True

    def read_calibration_mode(self):
        buf = bytearray([0x53, 0x06, 0x00])
        self.command(buf, 2)
        self.request(buf, 3)
        return buf[1]

    def set_manual_calibration(self, value):
        if value < 400 or value > 5000:
            return False
        buf = bytearray([0x52, 0x04, value >> 8, value & 0xFF, 0x00])
        buf[4] = self.crc8(buf[2:4])
        self.command(buf, 5)
        return True

    def crc8(self, arr, size):
        crc = 0xFF
        for b in range(size):
            crc ^= arr[b]
            for bit in range(0x80, 0, -1):
                if crc & 0x80:
                    crc <<= 1
                    crc ^= 0x31
                else:
                    crc <<= 1
        return crc

    def command(self, arr, size):
        result = self.i2c.writeto(self.address, bytes(arr))
        if result = None:
            self.error = 0
#             print('command success')
        else:
            self.error = result
#             print('command fail')
            
            
        return self.error


    def request(self, arr, size):
        bytes_received = self.i2c.readfrom_into(self.address, arr)
        if bytes_received == 0:
            self.error = -1
            return self._error
        if bytes_received < size:
            self.error = -2
            return self._error
        self.error = 0
        return self.error

