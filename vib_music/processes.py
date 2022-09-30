import wave
import multiprocessing
import numpy as np
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
        self.params = {}
        self.read_aud_len = 0
        # read streaming info from driver
        self.streaming = self.driver.streaming
        if self.streaming:
            try:
                self.wavefile = wave.open(self.driver.wavefile, "rb")
            except:
                print('cannot open audio file.')
                return
            self.audio_norm_scale = 1./float(1 << ((8 * self.wavefile.getsampwidth()) - 1))
            self.audio_channel_n = self.wavefile.getnchannels()
            self.read_aud_len = self.driver.fm.meta["len_sample"]
            self.params["len_window"] = self.driver.fm.features["stft"]["len_window"]
            self.params["len_hop"] = self.driver.fm.meta["len_hop"]
            self.params["sr"] = self.driver.fm.meta["sr"]
            self.params["global_scale"] = self.driver.fm.vib_kwargs_buffer.get("global_scale", 0.01)
            self.params["hprs_harmonic_filt_len"] = self.driver.fm.vib_kwargs_buffer.get("hprs_harmonic_filt_len", 0.1)
            if "hprs_percusive_filt_len" in self.driver.fm.vib_kwargs_buffer:
                self.params["hprs_percusive_filt_len"] = self.driver.fm.vib_kwargs_buffer.get("hprs_percusive_filt_len")
            self.params["hprs_beta"] = self.driver.fm.vib_kwargs_buffer.get("hprs_beta", 4.0)
            self.params["peak_globalth"] = self.driver.fm.vib_kwargs_buffer.get("peak_globalth", 20)
            self.params["peak_relativeth"] = self.driver.fm.vib_kwargs_buffer.get("peak_relativeth", 4)
            if "stft_peak_movlen" in self.driver.fm.vib_kwargs_buffer:
                self.params["stft_peak_movlen"] = int(self.driver.fm.vib_kwargs_buffer.get("stft_peak_movlen"))
            self.params["vib_extremefreq"] = self.driver.fm.vib_kwargs_buffer.get("vib_extreamfreq", [50,500])
            self.params["peak_limit"] = self.driver.fm.vib_kwargs_buffer.get("peak_limit", -1)
            self.params["vib_maxbin"] = self.driver.fm.vib_kwargs_buffer.get("vib_maxbin", 255)
            self.params["vib_bias"] = self.driver.fm.vib_kwargs_buffer.get("vib_bias", 80)
            self.params["duty"] = self.driver.fm.vib_kwargs_buffer.get("duty", 0.5)
            self.params["vib_frame_len"] = self.driver.fm.vib_kwargs_buffer.get("vib_frame_len", 24)
            self.params["stream_nwin"] = self.driver.fm.vib_kwargs_buffer.get("stream_nwin", 5)
            assert self.params["stream_nwin"]%2==1, "[ERROR] stream_nwin must be a odd number"

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
        if self.streaming is not None:
            self.stream.stop_stream()
            self.stream.close()

    def run(self):
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
                # self._init_audio_stream()
                start_switch = False    # flag indicating whether we start vibration
                read_start = 0    # steps after starting reading
                read_end = 0    # steps after ending reading
                map_buffer_len = self.params["stream_nwin"] * self.read_aud_len
                map_buffer = np.zeros((map_buffer_len))
                while True:
                    if self.sem.acquire(block=self.driver.blocking):
                        # print("read_start %d, read_end %d" % (read_start, read_end))
                        if not start_switch: start_switch = True    # one we recieve audio, we start vibration
                        # set audio read_len
                        if read_start==0:
                            # first reading, read half_map_buffer + 1 windows audio
                            read_len = (self.params["stream_nwin"]//2+1)*self.read_aud_len
                        else:
                            # not first freading, read 1 window audio
                            read_len = 1 * self.read_aud_len
                        # print("read_len is %d" % (read_len))
                        # read audio
                        raw_data = self.wavefile.readframes(read_len)
                        data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
                        data = data*self.audio_norm_scale
                        # TODO we don't use stereos now, only mono to match librosa load results
                        data = np.reshape(data, (-1, self.audio_channel_n))
                        data = np.mean(data,axis=-1)    # mix channels to mono
                        if len(raw_data)<=0 and read_end<self.params["stream_nwin"]//2:
                            # if we have no more audio, still read until we make the last audio window the center window of map_buffer
                            data = np.zeros((self.read_aud_len))
                        # store audio data
                        if read_start==0:
                            # first reading, put data into map_buffer, make the first audio window the center window of map_buffer
                            map_buffer[self.params["stream_nwin"]//2*self.read_aud_len:] = data
                            # print("skip len is %d" % (self.params["stream_nwin"]//2*self.read_aud_len))
                        else:
                            # not first reading, read one window audio to the map_buffer and shift the stored data by one window 
                            temp_buffer = map_buffer[self.read_aud_len:]
                            map_buffer[:len(temp_buffer)] = temp_buffer
                            map_buffer[len(temp_buffer):len(temp_buffer)+len(data)] = data
                            # print("skip len is %d" % (self.read_aud_len))
                        # mapping and vibrate
                        if len(raw_data) > 0 or read_end< self.params["stream_nwin"]//2:
                            # print(map_buffer.shape)
                            update = self.driver.on_running(update, map_buffer, self.params)
                        else: 
                            break
                        if len(raw_data)>0: read_start += 1    # increase step after starting reading
                        if len(raw_data)<=0: read_end += 1    # increase step after ending reading
                        if start_switch and not update: break    # once we start vibration, if we do not update, break

        self.driver.on_close()
        # self._clean_stream()
