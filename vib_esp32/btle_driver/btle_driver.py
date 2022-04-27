import sys

from bluepy import btle
from typing import Optional, Dict

sys.path.append('..')

from vib_music import StreamDriverBase
from vib_music import StreamEvent, StreamEventType

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
        self.tx_channel.write(what['frame'].tobytes(), withResponse=False)
    
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        return StreamEvent(StreamEventType.STREAM_STATUS_ACK, {'status': 'blte'})