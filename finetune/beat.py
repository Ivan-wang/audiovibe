from typing import Tuple
import numpy as np
from utils import tune_beat_parser
from utils import _main

from vib_music import MotorInvoker
from vib_music.config import init_board_invoker_config
from vib_music.config import init_vibration_extraction_config

@MotorInvoker.register_vibration_mode
def beatplp_mode(bundle: dict) -> Tuple[np.ndarray, np.ndarray]:
    pulse = bundle['beatplp']['data']
    bins = np.linspace(0., 1., 255, endpoint=True)
    amp = np.digitize(pulse, bins).astype(np.uint8)
    freq = np.ones_like(amp, dtype=np.uint8) * 64

    return (amp, freq)

def main():
    p = tune_beat_parser()
    opt = p.parse_args()
    print(opt)
    
    librosa_config = None
    plot_config = None
    invoker_config = None
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
            'vib_mode_func': beatplp_mode,
            'plots': ['beatplp']
        }

    if opt.task == 'run' or 'play':
        print('Prepare to Play Audio...')
        invoker_config = init_board_invoker_config()
        invoker_config['audio'] = opt.audio
        invoker_config['datadir'] = opt.data_dir
        invoker_config['motors'] = [
            ('console', {'show_none':False, 'show_frame': True}),
            ('board', {})
        ]
        invoker_config['vib_mode'] = 'beatplp_mode'

    _main(opt, librosa_config, invoker_config, plot_config)

main()