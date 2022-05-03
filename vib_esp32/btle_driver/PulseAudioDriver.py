import sys
import ctypes
from typing import Dict, Optional

sys.path.append('..')

from vib_music import StreamDriverBase
from vib_music import StreamEvent, StreamEventType

# use pulse audio driver for BT audio on raspberry pi
# to use this driver, you have to
# 1. install pulse audio and related bluetooth lib (not ALAS)
# 2. alreay paired the bluetooth speaker and set the audio output to it
# Note: 1st step is usually done by upgrade the raspberry pi OS


# HACK: directly load pulseaudio-simple C-lib into python
# Know Issue: cannot control volume from python
PA_STREAM_PLAYBACK = 1
PA_SAMPLE_S16LE = 3
BUFFSIZE = 1024

class struct_pa_sample_spec(ctypes.Structure):
    __slots__ = [
        'format',
        'rate',
        'channels',
    ]

struct_pa_sample_spec._fields_ = [
    ('format', ctypes.c_int),
    ('rate', ctypes.c_uint32),
    ('channels', ctypes.c_uint8),
]
pa_sample_spec = struct_pa_sample_spec  # /usr/include/pulse/sample.h:174

# check pulse audio lib installation
PULSE_AUDIO_LIB_READY = False
try:
    pa = ctypes.cdll.LoadLibrary('libpulse-simple.so.0')
except:
    PULSE_AUDIO_LIB_READY = False
else:
    PULSE_AUDIO_LIB_READY = True


class PulseAudioDriver(StreamDriverBase):
    def __init__(self) -> None:
        super(PulseAudioDriver, self).__init__()

        self.stream = None # Pulse Audio stream object
        self.error_ref = ctypes.c_int(0)
    
    def on_init(self, what:Dict) -> None:
        # create playback stream from spec
        ss = struct_pa_sample_spec()
        ss.rate = what['rate']
        ss.channels = what['channels']
        # ss.format = what['format']
        ss.format = PA_SAMPLE_S16LE # NOTE: hardcode here, need more information

        self.stream = pa.pa_simple_new(
            None,  # Default server.
            'VibMusic',  # Application's name, any
            PA_STREAM_PLAYBACK,  # Stream for playback.
            None,  # Default device.
            'playback',  # Stream's description.
            ctypes.byref(ss),  # Sample format.
            None,  # Default channel map.
            None,  # Default buffering attributes.
            ctypes.byref(self.error_ref)  # Ignore error code.
        )

        if not self.stream:
            self.stream = None
        
    def on_next_frame(self, what: Optional[Dict] = None) -> None:
        if what is not None:
            if (pa.pa_simple_write(self.stream, what['frame'], len(what['frame']), self.error_ref)):
                raise Exception('Pulse Audio Playing Error!')
        
    # TODO: report audio hardware status?
    def on_status_acq(self, what: Optional[Dict] = None) -> Optional[StreamEvent]:
        return StreamEvent(head=StreamEventType.STREAM_STATUS_ACK, what={'status': 'Music Stream'})
    
    def on_close(self, what: Optional[Dict] = None) -> None:
        # waiting from all sent data to finish playing
        pa.pa_simple_drain(self.stream, self.error_ref)
        # release resources
        pa.pa_simple_free(self.stream)
    
    # for simple-API, noting to do with pulse and resume
    def on_pulse(self, what: Optional[Dict] = None) -> None:
        pass

    def on_resume(self, what: Optional[Dict] = None) -> None:
        pass