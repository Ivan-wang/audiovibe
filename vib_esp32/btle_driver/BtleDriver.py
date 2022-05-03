import sys
import ctypes
from bluepy import btle
from enum import IntEnum
from typing import Optional, Dict

sys.path.append('..')

from vib_music import StreamDriverBase
from vib_music import StreamEvent, StreamEventType

class BtleEventType(IntEnum):
    DATA_FRAME = 0
    DATA_CLEAR = 1
    STATUS_ACQ = 2
    STATUS_ACK = 4

class btle_message(ctypes.Structure):
    __slots__ = ['head', 'len']

btle_message._fields_ = [
    ('head', ctypes.c_uint32),
    ('len', ctypes.c_uint32)
]

class BtleDriver(StreamDriverBase):
    def __init__(self) -> None:
        self.btle_addr = None
        self.btle_device = None

        self.tx_channel = None
        self.rx_channel = None
    
    def on_init(self, what: Optional[Dict] = None) -> None:
        self.btle_addr = what['btle_addr']

        try:
            self.btle_device = btle.Peripheral(self.btle_addr)
            self.btle_device.setMTU(400) # 400 bytes are sufficient large for 8 frames
        except btle.BTLEException:
            self.btle_device = None
        else:
            svc = self.btle_device.getServiceByUUID(what['service_uuid'])
            self.tx_channel = svc.getCharacteristics(what['tx_char_uuid'])[0]
            self.rx_channel = svc.getCharacteristics(what['rx_char_uuid'])[0]

    def on_close(self, what: Optional[Dict] = None) -> None:
        self.tx_channel = None
        self.rx_channel = None

        if self.btle_device is not None:
            self.btle_device.disconnect()
    
    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        if self.btle_device is None:
            return
        # send the entire array to blte device, do not need response
        data = what['frame'].tobytes()
        msg = btle_message(BtleEventType.DATA_FRAME, len(data))
        # NOTE: do not require response to save time
        self.tx_channel.write(bytes(msg)+data, withResponse=False)
    
    def on_pulse(self, what: Optional[Dict] = None) -> None:
        if self.btle_device is None:
            return
        # notify bluetooth device to clear cache
        msg = btle_message(BtleEventType.DATA_CLEAR)
        # NOTE: do not require response to save time
        self.tx_channel.write(bytes(msg), withResponse=False)
    
    def on_resume(self, what: Optional[Dict] = None) -> None:
        # notify bluetooth device 
        pass
    
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {'status': 'blte'})