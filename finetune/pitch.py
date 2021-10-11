import numpy as np

from utils import tune_pitch_parser, _main
from vib_music import FeatureManager
from vib_music.misc import init_vibration_extraction_config

@FeatureManager.vibration_mode
def pitch_drv2605(fm: FeatureManager) -> np.ndarray:
    if 'pitchyin' in fm.feature_names():
        pitch = fm.feature_data('pitchyin')
    else:
        pitch = fm.feature_data('pitchpyin')

    # pitch:
    # shape: [num frame x 1]
    # each entry is the estiamte base frequency of the frame
    amp = np.ones_like(pitch).astype(np.uint8) * 128
    freq = np.ones_like(pitch).astype(np.uint8) * 64

    return np.stack([amp, freq], axis=-1)

@FeatureManager.vibration_mode
def chroma_drv2605(fm: FeatureManager) -> np.ndarray:
    if 'chromastft' in fm.feature_names():
        chroma = fm.feature_data('chromastft')
    else:
        chroma = fm.feature_data('chromacqt')

    # chroma
    # shape: [num_frame x 12]
    #
    amp = np.ones((chroma.shape[0],)).astype(np.uint8) * 128
    freq = np.ones((chroma.shape[0],)).astype(np.uint8) * 64

    return np.stack([amp, freq], axis=-1)

@FeatureManager.vibration_mode
def pitch_sw(fm: FeatureManager) -> np.ndarray:
    if 'pitchyin' in fm.feature_names():
        pitch = fm.feature_data('pitchyin')
    else:
        pitch = fm.feature_data('pitchpyin')

    frame_len = fm.frame_len()
    sample_len = fm.sample_len()
    num_frame = (sample_len+frame_len-1) // frame_len
    return np.zeros((num_frame, 3), dtype=np.uint8)

@FeatureManager.vibration_mode
def chroma_sw(fm: FeatureManager) -> np.ndarray:
    if 'chromastft' in fm.feature_names():
        chroma = fm.feature_data('chromastft')
    else:
        chroma = fm.feature_data('chromacqt')

    frame_len = fm.frame_len()
    sample_len = fm.sample_len()
    num_frame = (sample_len+frame_len-1) // frame_len
    return np.zeros((num_frame, 3), dtype=np.uint8)

def main():
    p = tune_pitch_parser()
    opt = p.parse_args()
    print(opt)

    librosa_cfg = None
    plot_cfg = None

    if opt.task in ['run', 'build']:
        librosa_cfg = init_vibration_extraction_config()
        librosa_cfg['audio'] = opt.audio
        librosa_cfg['len_hop'] = opt.len_hop
        if opt.pitch:
            if opt.pitch_alg == 'pyin':
                librosa_cfg['stgs']['pitchpyin'] = {
                    'len_window': opt.len_window,
                    'fmin': opt.fmin,
                    'fmax': opt.fmax,
                }
            elif opt.pitch_alg == 'yin':
                librosa_cfg['stgs']['pitchyin'] = {
                    'len_window': opt.len_window,
                    'fmin': opt.fmin,
                    'fmax': opt.fmax,
                    'thres': opt.yin_thres
                }
            else:
                print(f'Unknown pitch axtraction algorithm {opt.pitch_alg}')
                return
        elif opt.chroma:
            if opt.chroma_alg == 'stft':
                librosa_cfg['stgs']['chromastft'] = {
                    'len_window': opt.len_window,
                    'n_chroma': opt.n_chroma,
                    'tuning': opt.tuning
                }
            elif opt.chroma_alg == 'cqt':
                librosa_cfg['stgs']['chromacqt'] = {
                    'fmin': opt.fmin,
                    'n_chroma': opt.n_chroma,
                    'tuning': opt.tuning,
                }
            else:
                print(f'Unknown chroma extraction algorithm {opt.chroma_alg}')
        else:
            print('Use --pitch or --chroma to finetune the picth features')
            return

    if opt.plot:
        feature = 'pitch' if opt.pitch else 'chroma'
        plot_cfg = {
            'plots': ['melspec', feature, 'vibration_drv2605']
        }

    vib_mode = 'pitch_drv2605' if opt.pitch else 'chroma_drv2605'
    _main(opt, vib_mode, 'drv2605', librosa_cfg, plot_cfg)

main()
