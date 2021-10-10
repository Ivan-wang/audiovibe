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
            format=audio.get_format_from_width(self.wavefile.getsampwidth()),
            channels = self.wavefile.getnchannels(),
            rate=self.wavefile.getframerate(),
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
                # release to vibration process
                self.vib_sem.release()
                # release to main process
                if self.proc_sem is not None: self.proc_sem.release()
                if self.stream is not None: self.stream.write(data)
            else:
                break

        self.proc_sem.release()
        print('audio playing exit...')
        self._clean_stream()

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
            if self.sem.acquire(block=False):
                update = True
            else:
                update = False

        self.driver.on_close()