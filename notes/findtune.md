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
*Option 2* in "findtune", run `python3 beat.py <other arguments>` (see next page)

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
