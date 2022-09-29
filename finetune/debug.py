import os, sys
import wave
from pyaudio import PyAudio
import numpy as np
import librosa
from librosa import stft
import struct

curr_path = os.getcwd()
in_aud = os.path.join(curr_path,"../audio/m1_cut_22k.wav")
frame_num = 192*3
len_window = 128
len_hop = 64

wavefile = wave.open(in_aud, "rb")
wave_data, _ = wavelibro = librosa.load(in_aud)

audio = PyAudio()

stream = audio.open(
    format=audio.get_format_from_width(wavefile.getsampwidth()),
    channels = wavefile.getnchannels(),
    rate=wavefile.getframerate(),
    output=True
)
# print(wavefile.getnframes())
# print(wave_data.shape)

wave_data = wave_data[:frame_num]
data = wavefile.readframes(frame_num)
return_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
scale = 1./float(1 << ((8 * wavefile.getsampwidth()) - 1))
return_data = return_data*scale
return_data = np.reshape(return_data, (-1, wavefile.getnchannels()))
return_data = np.mean(return_data,axis=-1)



y = np.pad(return_data, int(len_window // 2), mode='constant')
frames = librosa.util.frame(y, len_window, len_hop)

print(frames.shape[1])
sys.exit()
return_stft = stft(return_data, n_fft=len_window, hop_length=len_hop, win_length=len_window, window='hann',center=True, pad_mode='constant')
linspec = np.abs(return_stft)**2.0    # power linear spectrogram

feat_dim, feat_shape = linspec.shape

print(feat_shape)