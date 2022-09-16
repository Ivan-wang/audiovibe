import abc

class VibrationDriver(abc.ABC):
    def __init__(self, vibration_data=None) -> None:
        super(VibrationDriver, self).__init__()
        if vibration_data is None:
            self.vibration_iter = None
            self.vibration_len = 0
        else:
            self.vibration_len = len(vibration_data)
            self.vibration_iter = iter(vibration_data)

        self.device = None
        self.blocking = False

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

from .env import DRV2605_ENV_READY
if DRV2605_ENV_READY:
    import board
    import busio
    import adafruit_drv2605

class DR2605Driver(VibrationDriver):
    def __init__(self, vibrations, wavefile=None, fm=None, **kwargs) -> None:
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

from .env import ADC_ENV_READY
if ADC_ENV_READY:
    import smbus

# NOTE: each sample accept at most 8 operations
import numpy as np
class AdcDriver(VibrationDriver):
    def __init__(self, vibration_data=None, wavefile=None, fm=None, **kwargs) -> None:
        if isinstance(vibration_data, np.ndarray):
            if len(vibration_data.shape) > 2:
                print(f'vibration data should be at most 2D but get {vibration_data.shape}')
                vibration_data = None
        else:
            print(f'need a np.ndarray for vibration data but get {type(vibration_data)}')
            vibration_data = None
        super().__init__(vibration_data=vibration_data)

        # self.amp = 0

        # when use a sequence for each frame, set blocking mode as true
        if len(vibration_data.shape) > 2:
            self.blocking = False
        
        self.streaming = kwargs.get("streaming", False)
        if self.streaming:
            assert wavefile is not None, "[ERROR] wavefile must be provided under streaming"
            assert fm is not None, "[ERROR] FeatureManager must be passed under streaming"
        self.wavefile = wavefile
        self.fm = fm

    def on_start(self):
        if self.vibration_iter is None:
            return False

        if ADC_ENV_READY:
            self.device = smbus.SMBus(1)
            return True
        else:
            return False

    def on_running(self, update=False, data=None):
        if update:
            try:
                amp = next(self.vibration_iter)
            except StopIteration:
                return False
            else:
                if isinstance(amp, np.ndarray):
                    for a in amp:
                        self.device.write_byte_data(0x48, 0x40, a)
                else:
                    for _ in range(4):
                        self.device.write_byte_data(0x48, 0x40, amp)
                    self.device.write_byte_data(0x48, 0x40, 0)
        return True

    def on_close(self):
        # close the device?
        return
