import multiprocessing
from .FeatureExtractionManager import FeatureExtractionManager

def list_librosa_context():
    ks = list(FeatureExtractionManager.stg_funcs.keys())
    meta_ks = list(FeatureExtractionManager.stg_meta_funcs.keys())

    print(f'Available Librosa Strategies : {ks}')
    print(f'Available Librosa Meta Strategies : {meta_ks}')

def get_feature(features, k=None, prefix=None):
    if k is not None and k in features:
        return features[k]

    for name in features:
        if name.startswith(prefix):
            return features[name]

    return None

from .env import AUDIO_RUNTIME_READY
from .processes import AudioProcess

if AUDIO_RUNTIME_READY:
    import pyaudio
    import wave

def get_audio_process(audio, frame_len, sem, vib_sim=None):
    if not AUDIO_RUNTIME_READY:
        print('cannot import audio libs.')
        return None

    try:
        wf = wave.open(audio, 'rb')
    except:
        print('cannot open audio file.')
        return None

    return AudioProcess(wf, frame_len, sem, vib_sim)

from .processes import BoardProcess
from .drivers import DR2605Driver, AdcDriver, VibrationDriver
def get_board_process(driver:VibrationDriver, sem):
    if not driver.on_start():
        print('cannot initialize board.')
        return None
    return BoardProcess(driver, sem)

from .FeatureManager import FeatureManager
from tqdm import tqdm

def show_proc_bar(num_frame, sem):
    bar = tqdm(desc='[audio]', unit=' frame', total=num_frame)

    frame = 0
    while frame < num_frame:
        if sem.acquire(block=False):
            frame += 1
            bar.update()
    bar.close()

def launch_vibration(audio, feature_dir, mode, driver):
    fm = FeatureManager.from_folder(feature_dir, mode)

    if driver == 'drv2605':
        driver = DR2605Driver(fm.vibration_sequence())
    elif driver == 'adc':
        driver = AdcDriver(fm.vibration_sequence())
    else:
        print(f'unknown driver {driver}. exit...')
        return

    audio_sem = multiprocessing.Semaphore()
    vib_sem = multiprocessing.Semaphore()

    frame_len = fm.frame_len()
    audio_proc = get_audio_process(audio, frame_len, audio_sem, vib_sem)
    if audio_proc is None:
        print('initial audio process failed. exit...')
        return

    board_proc = get_board_process(driver, audio_sem)
    if board_proc is None:
        print('initial board process failed. exit...')
        return

    # show prograss bar here
    sample_len = fm.sample_len()
    num_frame = (sample_len + frame_len - 1) // frame_len

    board_proc.start()
    audio_proc.start()

    show_proc_bar(num_frame, vib_sem)

    board_proc.join()
    audio_proc.join()

from .plot import PlotManager
def launch_plotting(audio, feature_dir, mode, plots):
    fm = FeatureManager.from_folder(feature_dir, mode)
    if fm is None:
        print('cannot create feature manager')
        return
    ctx = PlotManager(audio, fm, plots)
    ctx.save_plots()

if __name__ == '__main__':
    list_librosa_context()