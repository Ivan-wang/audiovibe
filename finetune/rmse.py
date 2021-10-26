import numpy as np
from utils import tune_rmse_parser
from utils import _main

from vib_music import FeatureManager
from vib_music.misc import init_vibration_extraction_config

@FeatureManager.vibration_mode
def rmse_drv2605(fm:FeatureManager) -> np.ndarray:
    rmse = fm.feature_data('rmse')

    return np.zeros((2, rmse.shape[0]), dtype=np.uint8)

def main():
    p = tune_rmse_parser()
    opt = p.parse_args()
    print(opt)

    librosa_config = None
    plot_config = None
    if opt.task == 'run' or 'build':
        print('Buidling Feature Database...', end='')
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = opt.audio
        librosa_config['len_hop'] = opt.len_hop
        librosa_config['stgs']['rmse'] = {
            'len_window': opt.len_window,
        }

    if opt.plot:
        plot_config = {
            'plots': ['waveform', 'wavermse']
        }

    _main(opt, 'rmse_drv2605', 'drv2605', librosa_config, plot_config)

main()