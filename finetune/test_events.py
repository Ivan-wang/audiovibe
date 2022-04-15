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
from vib_music import PCF8591Driver
from vib_music import AudioStreamEvent, AudioStreamEventType

#
from vib_music import get_audio_process

fb = AudioFeatureBundle.from_folder('./test_fb')
sdata = VibrationStream.from_feature_bundle(fb, 24, 'rmse_mode')
sdriver = LogDriver()
# sdriver = PCF8591Driver()
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

commands.put(StreamEvent(head=StreamEventType.STREAM_INIT))
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

