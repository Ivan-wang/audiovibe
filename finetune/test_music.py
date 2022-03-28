import sys
from time import sleep, time
from multiprocessing import Queue
sys.path.append('..')

from vib_music import get_audio_process
from vib_music import StreamEvent, StreamEventType
from vib_music import AudioStreamEvent, AudioStreamEventType

results, commands = Queue(), Queue()

proc = get_audio_process('../audio/test_beat_short_1.wav', 512)
proc.set_event_queues(commands, results)
proc.start()

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

proc.join()