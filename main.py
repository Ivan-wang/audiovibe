from librosaContext import LibrosaContext
from vibrationEncoder import VibrationEncoder
from config import PLP_FRAME, FRAME_LEN
# from matplotlibInvoker import MatplotlibInvoker

import multiprocessing
import wave
import pyaudio
from tqdm import tqdm

# from config import WIN_LEN
from config import HOP_LEN
class AudioProcess(multiprocessing.Process):
    def __init__(self, filename, start_event, frame_event, frame_len, io_queue=None):
        super(AudioProcess, self).__init__()
        self.filename = filename
        self.frame_len = frame_len
        self.start_event = start_event
        self.frame_event = frame_event
    
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
            data = wf.readframes(self.frame_len)
            if len(data) > 0:
                self.frame_event.set()
                stream.write(data)
            else:
                break
        
        print('audio playing exit...')
        stream.stop_stream()
        stream.close()

class MotorProcess(multiprocessing.Process):
    def __init__(self, start_event, frame_event, total_frame):
        super(MotorProcess, self).__init__()
        self.start_event = start_event
        self.frame_event = frame_event
        self.total_frame = total_frame

    def run(self):
        bar = tqdm(desc='progress bar', unit=' frame', total=self.total_frame)
        self.start_event.set()

        for _ in range(self.total_frame):
            self.frame_event.wait()
            self.frame_event.clear()
            bar.update()

        bar.close()
        return


class BroadProcess(multiprocessing.Process):
    def __init__(self, vib_queue, invoker=None):
        super().__init__()
        self.vib_queue = vib_queue
        self.invoker = invoker
    
    def run(self):
        print('Feature Consumer Process Started..')
        self.invoker.on_start()

        while True:
            if not self.vib_queue.empty():
                vib = self.vib_queue.get()
                if vib is None:
                    print('Exiting Consumer Process...')
                    break
                else:
                    self.invoker.dispatch(vib)
        return

def main():
    frame_event = multiprocessing.Event()
    start_event = multiprocessing.Event()

    frame_len = HOP_LEN * 100
    num_sample = 2422560
    num_frame = num_sample // frame_len
    if num_sample % frame_len != 0:
        num_frame += 1
    audio_proc = AudioProcess('audio/YellowRiverSliced.wav', start_event, frame_event, frame_len)
    motor_proc = MotorProcess(start_event, frame_event, num_frame)

    audio_proc.start()
    motor_proc.start()
    motor_proc.join()
    audio_proc.join()

# call main function
main()