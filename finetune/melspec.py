import numpy as np
from utils import tune_melspec_parser
from utils import _main

from vib_music import FeatureManager
from vib_music.misc import init_vibration_extraction_config

@FeatureManager.vibration_mode
def melspec_drv2605(fm:FeatureManager) -> np.ndarray:
    spec = fm.feature_data('melspec')

    # freq_bins = np.linspace(0., 1., 10, endpoint=True)
    # freq = np.digitize(np.argmax(spec, axis=0), freq_bins).astype(np.uint8)
    print(np.argmax(spec, axis=0))

    freq = np.argmax(spec, axis=0).astype(np.float)
    freq = (freq / freq.max() * 128).astype(np.uint8)

    amp_bins = np.linspace(0., 1., 255, endpoint=True)
    amp = np.digitize(np.max(spec, axis=0), amp_bins).astype(np.uint8)

    vibration = np.stack([amp, freq], axis=-1)
    return vibration

@FeatureManager.vibration_mode
def melspec_sw(fm:FeatureManager) -> np.ndarray:
    # nothing here
    frame_len = fm.frame_len()
    sample_len = fm.sample_len()
    num_frame = (sample_len+frame_len-1) // frame_len
    return np.zeros((num_frame, 3), dtype=np.uint8)

def main():
    p = tune_melspec_parser()
    opt = p.parse_args()
    print(opt)

    librosa_config = None
    plot_config = None
    if opt.task == 'run' or 'build':
        print('Buidling Feature Database...', end='')
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = opt.audio
        librosa_config['len_hop'] = opt.len_hop
        librosa_config['stgs']['melspec'] = {
            'len_window': opt.len_window,
            'n_mels': opt.n_mels,
            'fmax': opt.fmax if opt.fmax > 0 else None
        }

    if opt.plot:
        plot_config = {
            'plots': ['melspec', 'vibration_drv2605']
        }

    _main(opt, 'melspec_drv2605', 'drv2605', librosa_config, plot_config)

main()