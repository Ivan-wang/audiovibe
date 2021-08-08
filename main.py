from boardInvoker import BoardInvoker
import motors #TODO: fix the dependency issue

import numpy as np
import multiprocessing
import wave
import pyaudio
from tqdm import tqdm

# from config import WIN_LEN
from config import BASE_HOP_LEN
class AudioProcess(multiprocessing.Process):
    def __init__(self, filename, motor_on, board_on, frame):
        super(AudioProcess, self).__init__()
        self.filename = filename
        self.motor_on = motor_on
        self.board_on = board_on
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
        
        self.motor_on.wait()
        self.motor_on.clear()

        self.board_on.wait()
        self.board_on.clear() 

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
    def __init__(self, invoker, motor_on, frame):
        super(MotorProcess, self).__init__()
        self.invoker = invoker
        self.motor_on = motor_on 
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

from multiprocessing import shared_memory
class BroadProcess(multiprocessing.Process):
    def __init__(self, buf_name, buf_lock, board_on):
        super().__init__()
        self.buf_name = buf_name
        self.buf_lock = buf_lock
        self.board_on = board_on
    
    def run(self):
        buf_mem = shared_memory.SharedMemory(name=self.buf_name).buf
        vib_buf = np.ndarray((8, ), dtype=np.uint8, buffer=buf_mem)
        vib_buf[2] = 5 # set buf[2] as real-time play mode

        i2c = busio.I2C(board.SCL, board.SDA)
        drv = adafruit_drv2605.DRV2605(i2c)
        drv._write_u8(0x1D, 0xA1) # enable LRA Open Loop Mode

        self.board_on.set()

        while True:
            self.buf_lock.acquire()

            if vib_buf[7] != 0:
                break
            # Set real-time play value (amplitude)
            drv._write_u8(0x02, vib_buf[0]) 
            # Set real-time play value (frequency)
            drv._write_u8(0x20, vib_buf[1]) 
            # Set real-time play mode
            drv._write_u8(0x01, 5) 

            drv.play()
        
        # drv.close()
        return


def init_vib_shm():
    vib_mem = np.zeors((8,), dtype=np.uint8)
    vib_shm = shared_memory.SharedMemory(create=True, size=vib_mem.nbytes)
    vib_mem_init = np.ndarray(vib_mem.shape, dtype=vib_mem.dtype, buf=vib_shm.buf)
    vib_mem_init[:] = vib_mem[:]

    return vib_shm.name

def main():
    # frame_event = multiprocessing.Event()
    vib_shm_name = init_vib_shm()
    vib_buf_lock = multiprocessing.Lock()
    frame = multiprocessing.Semaphore()
    motor_on = multiprocessing.Event()
    board_on = multiprocessing.Event()

    audioname = 'YellowRiverInstrument'
    motors = [('console', {'show_frame': True, 'show_none': False})]
    bid = BoardInvoker(audioname, motors=motors)

    audio_proc = AudioProcess('audio/YellowRiverInstrument.wav', motor_on, board_on, frame)
    motor_proc = MotorProcess(bid, motor_on, frame)
    board_proc = BoardProcess(buf_name=vib_shm_name, buf_lock=vib_buf_lock)

    audio_proc.start()
    motor_proc.start()
    motor_proc.join()
    audio_proc.join()

# call main function
main()