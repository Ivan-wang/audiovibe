import numpy as np
from utils import tune_rmse_parser
from utils import _main

from vib_music import FeatureManager
from vib_music.misc import init_vibration_extraction_config

@FeatureManager.vibration_mode
def rmse_voltage(fm:FeatureManager) -> np.ndarray:
    rmse = fm.feature_data('rmse')

    rmse = (rmse-rmse.min()) / (rmse.max()-rmse.min())
    rmse  = rmse ** 2

    bins = np.linspace(0., 1., 150, endpoint=True)
    level = np.digitize(rmse, bins).astype(np.uint8)

    # mimic a square wave for each frame [x, x, x, x, 0, 0, 0, 0]
    # [x,x,x,x,0,0,0,0,x,x,x,x,0,0,0,0,x,x,x,x,0,0,0,0] - 300Hz

    # when using 2D sequence, do not use plot function
    level_zeros = np.zeros_like(level)
    level_seq = np.stack([level]*4+[level_zeros]*4, axis=-1)
    level_seq = np.concatenate([level_seq]*3, axis=-1)

    return level_seq

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
            'plots': ['waveform', 'wavermse', 'vibration_adc']
        }

    _main(opt, 'rmse_voltage', 'adc', librosa_config, plot_config)

main()