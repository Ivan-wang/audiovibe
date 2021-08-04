---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.jpg')
marp: true
---

# **Project Notes**

---

# Time Synchronization

1. Audio $\rightarrow$ Sample Rate `sr`
2. Buffered IO $\rightarrow$ Chunk Size `cs` or `len_buf`
3. Audio Analyze $\rightarrow$ Window Length `wl` or `len_win`
    - Hop Length (window step) $\rightarrow$ `hop` or `len_hop`
        Note when `hop` == `wl`, there is no overlap between windows
    - Frame Length (number of window) $\rightarrow$ `fl` or `len_frame`
4. Vibration Duration
    - Timer based
    - IO based

---

# Audio analysis result to Vibration Duration

**Audio analysis** is based on window length, hop length and frame length.
**Audio playing** is based on real time.
**Vibration duration** is based on real time.

**Task: sync the feature sequence with real time**

---

# Audio Playing
In implementation, audio playing is based on `wave` and `pyaudio`

1. `wave` lib loads entire data into memory.
2. `pyaudio` builds a stream for output.
2. Manually split data by chunks (see `len_buf`) and send the chunk into the strem.

---
# Examplary Code

```python
wf = wave.open(filename, 'rb') # load audio
audio = pyaudio.PyAudio() # initialize device

# open stream
stream = audio.open(
    format=audio.get_format_from_width(wf.getsamplewidth()),
    channels = wf.getnchannels(),
    rate=wf.getframerate(),
    output=True
)

# split chunks and send data to the stream
while True:
    data = wf.readframes(CHUNK_SIZE)
    stream.write(data)
```
---

# Match Feature Sequence with Frame NO.

SR = 22050, HOP = 512, LEN_FRAME = 384, DURATION = 8.9s 
$$N_{\text{frame}} = N_{\text{sample}} / L_{hop}$$
$$T_{\text{frame}} = \frac{L_{\text{hop}}\times L_{\text{frame}}}{SR}$$

---
# `librosa` time and frame utils

`librosa.time_to_frame`: time $\rightarrow$ frame number
`librosa.frames_to_time`: frame number $\rightarrow$ time (in second)
`librosa.samples_to_frames`: sample index $\rightarrow$ frame number
`librosa.frame_to_samples`: frame number $\rightarrow$  sample index 
`librosa.times_like`: data points $\rightarrow$ frame number $\rightarrow$ time (in second)

---

4732 Frames