import logging
import sys
from typing import Tuple
import numpy as np

from utils import tune_pitch_parser, _main
from vib_music import MotorInvoker
from vib_music.config import init_board_invoker_config
from vib_music.config import init_vibration_extraction_config

@MotorInvoker.register_vibration_mode
def handle_pitch(bundle: dict) -> Tuple[np.ndarray, np.ndarray]:
    if 'pitchyin' in bundle:
        pitch = bundle['pitchyin']['data']
    else:
        pitch = bundle['pitchpyin']['data']

    # pitch:
    # shape: [num frame x 1]
    # each entry is the estiamte base frequency of the frame
    amp = np.ones_like(pitch).astype(np.uint8) * 128
    freq = np.ones_like(pitch).astype(np.uint8) * 64

    return amp, freq

@MotorInvoker.register_vibration_mode
def handle_chroma(bundle: dict) -> Tuple[np.ndarray, np.ndarray]:
    if 'chromastft' in bundle:
        chroma = bundle['chromastft']['data']
    else:
        chroma = bundle['chromacqt']['data']

    # chroma
    # shape: [num_frame x 12]
    #
    amp = np.ones((chroma.shape[0],)).astype(np.uint8) * 128
    freq = np.ones((chroma.shape[0],)).astype(np.uint8) * 64

    return amp, freq

def main():
    p = tune_pitch_parser()
    opt = p.parse_args()

    logger = logging.getLogger('finetune')
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s][%(message)s]')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info('commond line arguments:')
    logger.info(opt)

    librosa_cfg = None
    plot_cfg = None
    invoker_cfg = None

    logger.info('building configure...')
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
                logger.error(f'Unknown pitch axtraction algorithm {opt.pitch_alg}')
                return
        elif opt.chroma:
            if opt.chroma_alg == 'stft':
                librosa_cfg['stgs']['chromastft'] = {
                    'len_window': opt.len_window
                }
            elif opt.chroma_alg == 'cqt':
                librosa_cfg['stgs']['chromacqt'] = {
                    'fmin': opt.fmin
                }
            else:
                logger.error(f'Unknown chroma extraction algorithm {opt.chroma_alg}')
        else:
            logger.error('Use --pitch or --chroma to finetune the picth features')
            return

    if opt.plot:
        plot_cfg = {
            'datadir': opt.data_dir,
            'audio': opt.audio,
            'vib_mode_func': handle_pitch if opt.pitch else handle_chroma,
            'plots': ['pitch' if opt.pitch else 'chroma']
        }

    if opt.task in ['run', 'play']:
        invoker_cfg = init_board_invoker_config()
        invoker_cfg['audio'] = opt.audio
        invoker_cfg['datadir'] = opt.data_dir
        invoker_cfg['motors'] = [
            ('console', {'show_none':True, 'show_frame': True}),
            ('board', {})
        ]
        invoker_cfg['vib_mode'] = 'handle_pitch' if opt.pitch else 'handle_chroma'
    logger.info('Done!')

    _main(opt, librosa_cfg, invoker_cfg, plot_cfg)

main()
