import sys
import keyboard
from time import sleep, time
from multiprocessing import Queue
sys.path.append('..')

from vib_music import get_audio_process
from vib_music import StreamEvent, StreamEventType
from vib_music import AudioStreamEvent, AudioStreamEventType

keyboard.on_press_key(keyboard.KEY_UP, lambda : print('UP Key Pressed'))

keyboard.wait()
