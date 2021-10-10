import wave
import multiprocessing

AUDIO_RUNTIME_READY = False
try:
    import pyaudio
except ImportError:
    AUDIO_RUNTIME_READY = False
else:
    AUDIO_RUNTIME_READY = True
    from pyaudio import PyAudio


DRV2605_ENV_READY = False
try:
    import board
    import busio
    import adafruit_drv2605
except ImportError:
    pass
else:
    DRV2605_ENV_READY = True

SQUARE_WAVE_ENV_READY = False
try:
    import smbus
except ImportError:
    pass
else:
    SQUARE_WAVE_ENV_READY = True

class AudioProcess(multiprocessing.Process):
    def __init__(self, wavefile, frame_len, vib_sem, proc_sem=None):
        super(AudioProcess, self).__init__()
        self.wavefile= wavefile
        self.frame_len = frame_len
        self.vib_sem = vib_sem
        self.proc_sem = proc_sem

        self.stream = None

    def _init_audio_stream(self):
        from pyaudio import PyAudio
        audio = PyAudio()
        self.stream = audio.open(
            format=audio.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True
        )

    def _clean_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()

    def run(self):
        # IMPORTANT: initialize the audio within one process
        # Don't share it across different processes
        self._init_audio_stream()

        print('start to play audio...')
        while True:
            data = self.wavefile.readframes(self.frame_len)
            if len(data) > 0:
                self.vib_sem.release() # release data here
                if self.proc_sem is not None: self.proc_sem.release()
                if self.stream is not None: self.stream.write(data)
            else:
                break

        self.frame.release()
        print('audio playing exit...')
        self._clean_stream()

# class MotorProcess(multiprocessing.Process):
#     def __init__(self, invoker):
#         super(MotorProcess, self).__init__()
#         self.invoker = invoker
#         self.motor_on = None
#         self.frame = None

#         self.vib_queue = multiprocessing.Queue()
#         self.board_off = multiprocessing.Event()

#     def attach(self, audio_proc):
#         if not isinstance(audio_proc, AudioProcess):
#             raise TypeError('MotorProcess can ONLY be attached to an AudioProcess')
#         self.motor_on = audio_proc.motor_on
#         self.frame = audio_proc.frame
#         self.total_frame = audio_proc.frame

#     def run(self):
#         if self.motor_on is None or self.frame is None:
#             print('Please Attach Motor Process to an Audio Process Before Start!')
#             return

#         self.invoker.on_start(self)
#         self.motor_on.set() # release the audio process

#         for _ in range(self.invoker.num_frame):
#             self.frame.acquire()
#             self.invoker.on_update()
#         self.invoker.on_end()

#         self.board_off.wait()
#         print('Motor Process Exit...')
#         return

from .drivers import VibrationDriver
class BoardProcess(multiprocessing.Process):
    def __init__(self, driver:VibrationDriver, sem:multiprocessing.Semaphore):
        super().__init__()
        self.sem = sem
        self.driver = driver

    def run(self):
        # self.driver.on_start()
        update = False
        while self.driver.on_running(update):
            if self.sem.locked():
                update = False
            else:
                self.sem.acquire()
                update = True

        self.driver.on_close()