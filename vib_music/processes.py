import wave
import multiprocessing

class AudioProcess(multiprocessing.Process):
    def __init__(self, filename, hop_len):
        super(AudioProcess, self).__init__()
        self.filename = filename
        self.hop_len = hop_len

        self.motor_on = multiprocessing.Event()
        self.board_on = multiprocessing.Event()
        self.frame = multiprocessing.Semaphore()

    def run(self):
        print('init feature proc...')
        # IMPORTANT: initialize the audio within one process
        # Don't share it across different processes
        wf = wave.open(self.filename, 'rb')
        try:
            import pyaudio

            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=audio.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
        except ImportError:
            stream = None

        # print(f'Sample Rate {wf.getframerate()}')
        # print(f'Num of Frame {wf.getnframes()}')
        # print('loaded wav file...')

        self.motor_on.wait()
        self.motor_on.clear()

        self.board_on.wait()
        self.board_on.clear()

        print('start to play audio...')
        while True:
            data = wf.readframes(self.hop_len)
            if len(data) > 0:
                self.frame.release()
                if stream is not None: stream.write(data)
            else:
                break

        self.frame.release()
        print('audio playing exit...')
        if stream is not None:
            stream.stop_stream()
            stream.close()

class MotorProcess(multiprocessing.Process):
    def __init__(self, invoker):
        super(MotorProcess, self).__init__()
        self.invoker = invoker
        self.motor_on = None
        self.frame = None

        self.vib_queue = multiprocessing.Queue()
        self.board_off = multiprocessing.Event()

    def attach(self, audio_proc):
        if not isinstance(audio_proc, AudioProcess):
            raise TypeError('MotorProcess can ONLY be attached to an AudioProcess')
        self.motor_on = audio_proc.motor_on
        self.frame = audio_proc.frame
        self.total_frame = audio_proc.frame

    def run(self):
        if self.motor_on is None or self.frame is None:
            print('Please Attach Motor Process to an Audio Process Before Start!')
            return

        self.invoker.on_start(self)
        self.motor_on.set()

        for _ in range(self.invoker.total_frame):
            self.frame.acquire()
            self.invoker.on_update()
        self.invoker.on_end()

        self.board_off.wait()
        print('Motor Process Exit...')
        return

_BOARD_ENV_READY = False
try:
    import board
    import busio
    import adafruit_drv2605
    _BOARD_ENV_READY = True
    print('Board Env Ready!')
except ImportError:
    print('Board Env Missing!')

class BoardProcess(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.vib_queue = None
        self.board_on = None
        self.board_off = None

    def attach(self, audio_proc, motor_proc):
        self.board_on = audio_proc.board_on
        self.board_off = motor_proc.board_off
        self.vib_queue = motor_proc.vib_queue

    def run(self):
        if self.vib_queue is None or self.board_on is None:
            print('Please Attach Board Process to an AudioProcess and a MotorProcess Before Start!')

        if _BOARD_ENV_READY:
            i2c = busio.I2C(board.SCL, board.SDA)
            drv = adafruit_drv2605.DRV2605(i2c)
            drv._write_u8(0x1D, 0xA1) # enable LRA Open Loop Mode
        else:
            print('Board Env Not Ready, Dry-run Board Process...')

        self.board_on.set()
        last_amp, last_freq, last_end = 0, 0, False

        while True:
            try:
                amp, freq, end = self.vib_queue.get(block=False)
            except:
                amp, freq, end = last_amp, last_freq, last_end
            else:
                last_amp, last_freq, last_end = amp, freq, end

            if end:
                break

            if _BOARD_ENV_READY:
                # Set real-time play value (amplitude)
                drv._write_u8(0x02, amp)
                # Set real-time play value (frequency)
                drv._write_u8(0x20, freq)
                # Set real-time play mode
                drv._write_u8(0x01, 5)
                drv.play()

        # drv.close()
        self.board_off.set()
