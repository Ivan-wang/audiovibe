import abc

class VibrationDriver(abc.ABC):
    def __init__(self, vibration_data=None) -> None:
        super(VibrationDriver, self).__init__()
        self.vibration_len = len(vibration_data)
        self.vibration_iter = iter(vibration_data)

        self.device = None

    def __len__(self):
        return self.vibration_len

    @abc.abstractmethod
    def on_start(self):
        return

    @abc.abstractmethod
    def on_running(self, update=False):
        return

    @abc.abstractmethod
    def on_close(self):
        return

DRV2605_ENV_READY = False
try:
    import board
    import busio
    import adafruit_drv2605
except ImportError:
    pass
else:
    DRV2605_ENV_READY = True

class DR2605Driver(VibrationDriver):
    def __init__(self, vibrations) -> None:
        if (vibrations.shape[1] != 2):
            vibrations = None
        super().__init__(vibration_data=vibrations)

        self.amp = 0
        self.freq = 0

    def on_start(self):
        if DRV2605_ENV_READY:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.device = adafruit_drv2605.DRV2605(i2c)
            self.device._write_u8(0x1D, 0xA1) # enable LRA Open Loop Mode
            return True
        else:
            return False

    def on_running(self, update=False):
        if update:
            try:
                self.amp, self.freq = next(self.vibration_iter)
            except StopIteration:
                return False
        self.device._write_u8(0x02, self.amp) # Set real-time play value (amplitude)
        self.device._write_u8(0x20, self.freq) # Set real-time play value (frequency)
        self._write_u8(0x01, 5) # Set real-time play mode
        self.device.play()
        return True

    def on_close(self):
        self.device._write_u8(0x01, 0)

SQUARE_WAVE_ENV_READY = False
try:
    import smbus
except ImportError:
    pass
else:
    SQUARE_WAVE_ENV_READY = True

import time
class SquareWaveDriver(VibrationDriver):
    def __init__(self, vibration_data=None) -> None:
        super().__init__(vibration_data=vibration_data)

        self.amp = 0
        self.act_time = 0
        self.cycle_time = 0
    def on_start(self):
        if SQUARE_WAVE_ENV_READY:
            self.device = smbus.SMBus(1)
            return True
        else:
            return False

    def on_running(self, update=False):
        if update:
            try:
                self.amp, self.act_time, self.cycle_time = next(self.vibration_iter)
            except StopIteration:
                return False
        self.device.write_byte_data(0x48, 0x40, self.amp)
        time.sleep(self.activate)
        self.device.write_byte_data(0x48, 0x40, 0)
        time.sleep(self.cycle-self.activate)
        return True
