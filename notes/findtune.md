---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.jpg')
marp: true
---
# Finetune Notes

---
## Project Folders

```
/root
    /vib_music -----> source files
    /notes     -----> project notes
    /finetune  -----> debug and findtune feature extraction
        /beat.py    -----> funetune beat features
    /audio
    /data
    main.sh    -----> shortcut bash script to call "beat.py"
```
**To run:**
*Option 1* in "root" directory, run `bash main.sh`
*Option 2* in "findtune", run `python3 <finetune_script>.py <other arguments>`

---
## Arguments for "Beat PLP"
**core function** : `librosa.beat.plp`
**arguments (from command line)**:
1. `--len-hop`: hop length
2. `--len-frame`: frame length (according to `librosa`, "frame length" is the number of hops in one frame)
$$N_{\text{samples\_in\_frame}} = \text{len\_hop}\times \text{len\_frame}$$
3. `--min-tempo`, `--max-tempo`: min and max tempo to be extracted

---
## Control the hardware
* `librosa` extract pulse from the audio, a $(N_{\text{frame}}\times 1)$ `np.ndarray`
* hardware motors accepts `amp` and `freq` as the controls signals for each frame. (both `amp` and `freq` are `np.uint8` scalar)
* to control the hardhware, define a callback function with the following signature
```python
def handle_pulse(pulse: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
```
---
## Callback function example
This is the default behavior of `handle_pulse`:

```python
def handle_pulse(pulse: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    # create 256 bins and digitize each pulse value
    bins = np.linspace(0., 1., 256, endpoint=True)
    amp = np.digitize(pulse, bins).astype(np.uint8)
    # set 64 as the constant freq for all frame
    freq = np.ones_like(amp, dtype=np.uint8) * 64

    return (amp, freq)
```
--- 
## Pass callback function to `MotorInvoker`
(Already Done in `beat.py`)
```python
#...
        invoker_config['iter_kwargs'] = {
            'beatplp': {'vib_func': handle_pulse}
        }
#...
```
---
## Arguments to finetune pitch related features
**1. Finetune Pitch Extraction**
(1) use `--pitch` to toggle pitch finetune switch
(2) use `--pitch-alg` to choose the algorithm from `{pyin, yin}` (default: `pyin`)
(3) use `--fmin` and `--fmax` to set the frequency range by note name. (default: from `C2` to `C7`)
(4) use `--len-window` to set FFT window length. (default: 2048)
(5) for `yin` algorithm, use `--yin-thres` to set threshold. (default: 0.8)

---

**Command Example (in `main.bash`):**

```bash
python3 pitch.py --task run --audio "xxx.wav" \
    --pitch --pitch-alg pyin --fmin C2 --fmax C7 \
    --len-window 2048

```

---

**2. Finetune Chromagram**
(1) use `--chroma` to toggle chromagram finetune switch
(2) use `--chroma-alg` to choose algorithm from `{stft, cqt}`
Note: `cqt` computes "Constant-Q chromagram"
(3) use `--n-chroma` to set the number of chroma bins to produce. (default: 12)
(4) use `--tuning` to set the deviation (in fractions of a CQT bin) from A440 tuning. (default: 0.0)
$$
\text{Ref\_Freq} = 440 \times 2^{\text{tuning}/{\text{bins-per-octave}}}
$$
(5) use `--len-window` to set FFT window length. (default: 2048)
(6) for `cqt` algoritm, use `fmin` to set the lower frequence bound. (default: `C2`)

---

**Command Example (in `main.bash`):**

```bash
python3 pitch.py --task run --audio "xxx.wav" \
    --chroma --chroma-alg stft --n-chroma 12 \
    --tuning 0.0 --len-window 2048

```
---
**Callback function example to handle chromagram**
*all examples are in `pitch.py`, check the comments bellow for the usage and data types.*
```python

# register the vibration mode to invoker
@MotorInvoker.register_vibration_mode
def handle_chroma(bundle: dict) -> Tuple[np.ndarray, np.ndarray]:
    # obtain the chroma matrix, usually don't need to change it.
    if 'chromastft' in bundle:
        chroma = bundle['chromastft']['data']
    else:
        chroma = bundle['chromacqt']['data']

    # chroma matrix has the following properities
    # shape: [num_frame x num_chroma_bins] (time x chroma)
    # data type: float32 in range [0, 1]. The normalized energy in each chroma bin.
```

---

```python

    # the following two lines simplely set the amp as 128 and freq as 64
    # implement the vibration method here and replace the following two lines.
    amp = np.ones((chroma.shape[0],)).astype(np.uint8) * 128
    freq = np.ones((chroma.shape[0],)).astype(np.uint8) * 64

    return amp, freq
```
---

