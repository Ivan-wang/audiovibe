from utils import tune_pitch_parser, _main
from typing import Tuple
import numpy as np

from vib_music import LibrosaContext
from vib_music.config import init_board_invoker_config
from vib_music.config import init_vibration_extraction_config

def handle_pitch():
    pass

def handle_chrome():
    pass

def main():
    p = tune_pitch_parser()
    opt = p.parse_args()
    print(opt)

    librosa_cfg = None
    invoker_cfg = None

    if opt.task in ['run', 'build']:
        librosa_cfg = init_vibration_extraction_config()
        librosa_cfg['audio'] = opt.audio
        librosa_cfg['len_hop'] = opt.len_hop
        if opt.pYIN:
            librosa_cfg['stgs']['pitchpyin'] = {
                'len_window': opt.len_window,
                'fmin': opt.fmin,
                'fmax': opt.fmax,
            }
        else:
            librosa_cfg['stgs']['pitchpyin'] = {
                'len_window': opt.len_window,
                'fmin': opt.fmin,
                'fmax': opt.fmax,
                'thres': opt.yin_thres
            }
        
    if opt.task in ['run', 'play']:
        invoker_cfg = init_board_invoker_config()
    
    _main(opt, librosa_cfg, invoker_cfg)

main()
