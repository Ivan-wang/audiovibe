from scipy.io.wavfile import write
import numpy as np


samplerate = 44100
fs = 100
dura = 2

t = np.linspace(0., float(dura), samplerate)
amplitude = np.iinfo(np.int16).max
data = amplitude * np.sin(2. * np.pi * fs * t)
write("example_sine.wav", samplerate, data.astype(np.int16))

t_1 = np.ones((samplerate*dura))
data_fixed = max(data)*t_1
write("example_fixed.wav", samplerate, data_fixed.astype(np.int16))
