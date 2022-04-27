import sys
import numpy as np
from time import sleep
from multiprocessing import Queue

sys.path.append('..')

from vib_music import AudioFeatureBundle
from vib_music import VibrationStream
from vib_music import LogDriver
from vib_music import StreamHandler
from vib_music import VibrationProcess
from vib_music import StreamEvent, StreamEventType
from vib_music import AudioStreamEvent, AudioStreamEventType
from vib_music import get_audio_process

from btle_driver import BtleDriver
BTLE_ADDR = "44:17:93:59:3F:92"
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
TX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
RX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

fb = AudioFeatureBundle.from_folder('../data/test_fb')
sdata = VibrationStream.from_feature_bundle(fb, 24, 'rmse_mode')
sdriver = BtleDriver()
# sdriver = LogDriver()
shandler = StreamHandler(sdata, sdriver)
vib_proc = VibrationProcess(shandler)

audio = '../audio/test_beat_short_1.wav'
len_hop = 512
music_proc = get_audio_process(audio, len_hop)

results, commands = Queue(), Queue()
music_proc.set_event_queues(commands, results)
music_proc.attach_vibration_proc(vib_proc)

vib_proc.start()
music_proc.start()

init_info = {
    'btle_addr': BTLE_ADDR,
    'service_uuid': SERVICE_UUID,
    'tx_char_uuid': TX_CHAR_UUID,
    'rx_char_uuid': RX_CHAR_UUID 
}
commands.put(StreamEvent(head=StreamEventType.STREAM_INIT, what=init_info))
commands.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_START))
sleep(1)
commands.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': 250}))
sleep(1)
commands.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_PULSE))
sleep(1)
commands.put(AudioStreamEvent(head=AudioStreamEventType.STREAM_SEEK, what={'pos': 250}))
commands.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_RESUME))
sleep(1)
commands.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_PULSE))
sleep(1)
commands.put(AudioStreamEvent(head=AudioStreamEventType.AUDIO_RESUME))
# commands.put(StreamEvent(head=StreamEventType.STREAM_CLOSE))

vib_proc.join()
print('vibration proc joined!')
music_proc.join()
print('music proc joined!')
