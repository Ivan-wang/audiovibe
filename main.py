from boardInvoker import BoardInvoker
import motors #TODO: fix the dependency issue

import multiprocessing
import wave
import pyaudio
from tqdm import tqdm

# from config import WIN_LEN
from config import BASE_HOP_LEN
class AudioProcess(multiprocessing.Process):
    def __init__(self, filename, start_event, frame):
        super(AudioProcess, self).__init__()
        self.filename = filename
        self.start_event = start_event
        self.frame = frame
    
    def run(self):
        print('init feature proc...')
        # IMPORTANT: initialize the audio within one process
        # Don't share it across different processes
        audio = pyaudio.PyAudio()
        wf = wave.open(self.filename, 'rb')
        print(f'Sample Rate {wf.getframerate()}')
        print(f'Num of Frame {wf.getnframes()}')
        print('loaded wav file...')

        stream = audio.open(
            format=audio.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        self.start_event.wait()
        self.start_event.clear()

        print('start to play audio...')
        while True:
            data = wf.readframes(BASE_HOP_LEN)
            if len(data) > 0:
                self.frame.release()
                stream.write(data)
            else:
                break
        
        print('audio playing exit...')
        stream.stop_stream()
        stream.close()

class MotorProcess(multiprocessing.Process):
    def __init__(self, invoker, start_event, frame):
        super(MotorProcess, self).__init__()
        self.invoker = invoker
        self.start_event = start_event
        self.frame = frame

        self.total_frame = self.invoker.meta['len_sample'] // BASE_HOP_LEN
        if self.invoker.meta['len_sample'] % BASE_HOP_LEN != 0:
            self.total_frame += 1

    def run(self):
        self.invoker.on_start()

        self.start_event.set()

        for _ in range(self.total_frame):
            self.frame.acquire()
            self.invoker.on_update()

        self.invoker.on_end()
        return

import board
import busio
import adafruit_drv2605

class BroadProcess(multiprocessing.Process):
    def __init__(self, buf_name, vib_lock):
        super().__init__()
        self.buf_name = buf_name
        self.vib_lock = vib_lock
    
    def run(self):
        print('Feature Consumer Process Started..')
        i2c = busio.I2C(board.SCL, board.SDA)
        drv = adafruit_drv2605.DRV2605(i2c)
        buf = shared_memory.SharedMemory(name=self.buf_name).buf
        vib_sequence = np.ndarray((8, ), dtype=np.uint8, buffer=buf)

        while True:
            # acquire lock
            if vib_sequence[-1] != 0:
                break
            for i in range(8):
                drv.sequence[i] = vib_sequence[i]
            drv.play()
        return

def main():
    # frame_event = multiprocessing.Event()

    frame = multiprocessing.Semaphore()
    start_event = multiprocessing.Event()
    

    audioname = 'YellowRiverInstrument'
    motors = [('console', {'show_frame': True, 'show_none': False})]
    bid = BoardInvoker(audioname, motors=motors)

    audio_proc = AudioProcess('audio/YellowRiverInstrument.wav', start_event, frame)
    motor_proc = MotorProcess(bid, start_event, frame)

    audio_proc.start()
    motor_proc.start()
    motor_proc.join()
    audio_proc.join()

# call main function
main()