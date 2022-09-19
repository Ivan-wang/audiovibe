import wave
import multiprocessing

from .env import AUDIO_RUNTIME_READY

if AUDIO_RUNTIME_READY:
    from pyaudio import PyAudio

class AudioProcess(multiprocessing.Process):
    def __init__(self, wavefile, frame_len, vib_sem, proc_sem=None, fm=None):
        super(AudioProcess, self).__init__()
        self.wavefile= wavefile
        self.frame_len = frame_len
        self.vib_sem = vib_sem
        self.proc_sem = proc_sem

        self.streaming = None
        self.read_aud_len = self.frame_len    # by default only read 1 frame audio
        if not fm:
            self.streaming = fm.streaming
            if self.streaming: self.read_aud_len = fm.meta["len_sample"]    # if streaming, read audio of specified length

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
            data = self.wavefile.readframes(self.read_aud_len)
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
        self.wavefile = None
        self.fm = None
        self.read_aud_len = 0
        # read streaming info from driver
        self.streaming = self.driver.streaming
        if self.streaming:
            self.wavefile = self.driver.wavefile
            self.fm = self.driver.fm
            self.read_aud_len = self.fm.meta["len_sample"]

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
        self._init_audio_stream()
        start_switch = False    # flag indicating whether we start vibration

        # driver starting before creating the board process
        # self.driver.on_start()
        if self.sem is None:
            print('Running in stand-alone mode')
            while self.driver.on_running(True):
                pass
        else:
            update = False
            if not self.streaming:
                while self.driver.on_running(update):
                    if self.sem.acquire(block=self.driver.blocking):
                        update = True
                    else:
                        update = False
            else:
                while True:
                    if self.sem.acquire(block=self.driver.blocking):
                        if not start_switch: start_switch = True    # one we recieve audio, we start vibration
                        data = self.wavefile.readframes(self.read_aud_len)
                        if len(data) > 0:
                            update = self.driver.on_running(update, data, self.fm)
                        else: break
                        if start_switch and not update: break    # once we start vibration, if we do not update, break

        self.driver.on_close()
        self._clean_stream()
