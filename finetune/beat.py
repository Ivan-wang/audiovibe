from typing import Tuple
import numpy as np
from numpy.core.shape_base import stack
from utils import tune_beat_parser
from utils import _main

from vib_music import FeatureManager, features
from vib_music.config import init_board_invoker_config
from vib_music.config import init_vibration_extraction_config

@FeatureManager.vibration_mode
def beatplp_drv2605(fm:FeatureManager) -> np.ndarray:
    pulse = fm.feature_data('beatplp')
    bins = np.linspace(0., 1., 255, endpoint=True)
    amp = np.digitize(pulse, bins).astype(np.uint8)
    freq = np.ones_like(amp, dtype=np.uint8) * 64
    vibration = np.stack([amp, freq], stack=-1)
    return vibration

@FeatureManager.vibration_mode
def beatplp_sw(fm:FeatureManager) -> np.ndarray:
    frame_len = fm.frame_len()
    sample_len = fm.sample_len()
    num_frame = (sample_len+frame_len-1) // frame_len
    return np.zeros((num_frame, 3), dtype=np.uint8)

def main():
    p = tune_beat_parser()
    opt = p.parse_args()
    print(opt)

    librosa_config = None
    plot_config = None
    if opt.task == 'run' or 'build':
        print('Buidling Feature Database...', end='')
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = opt.audio
        librosa_config['len_hop'] = opt.len_hop
        librosa_config['stgs']['beatplp'] = {
            'len_frame': opt.len_frame,
            'tempo_min': opt.min_tempo,
            'tempo_max': opt.max_tempo
        }

    if opt.plot:
        plot_config = {
            'datadir': opt.data_dir,
            'audio': opt.audio,
            'vib_mode_func': beatplp_drv2605,
            'plots': ['beatplp']
        }

    _main(opt, 'beatplp_drv2605', 'drv2605', librosa_config, plot_config)

main()