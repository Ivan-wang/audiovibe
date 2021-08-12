import sys
sys.path.append('..')

from typing import Tuple
import numpy as np
from utils import tune_beat_parser

from vib_music import LibrosaContext
from vib_music import MotorInvoker
from vib_music import AudioProcess, BoardProcess, MotorProcess
from vib_music.config import init_board_invoker_config
from vib_music.config import init_vibration_extraction_config

def handle_pulse(pulse: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    bins = np.linspace(0., 1., 256, endpoint=True)
    amp = np.digitize(pulse, bins).astype(np.uint8)
    freq = np.ones_like(amp, dtype=np.uint8) * 64

    return (amp, freq)

def main():
    p = tune_beat_parser()
    opt = p.parse_args()
    print(opt)

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
        ctx = LibrosaContext.from_config(librosa_config)
        ctx.save_features(root=opt.data_dir)
        print('Done!')

    if opt.task == 'run' or 'play':
        print('Prepare to Play Audio...')
        invoker_config = init_board_invoker_config()
        invoker_config['audio'] = opt.audio
        invoker_config['datadir'] = opt.data_dir
        invoker_config['motors'] = [
            ('console', {'show_none':False, 'show_frame': True}),
            ('board', {})
        ]
        invoker_config['iter_kwargs'] = {
            'beatplp': {'vib_func': handle_pulse}
        }

        print('Loading Vibration Database...')
        invoker = MotorInvoker.from_config(invoker_config)
        print('Init Processes...')
        audio_proc = AudioProcess(opt.audio, opt.len_hop)
        motor_proc = MotorProcess(invoker)
        board_proc = BoardProcess()

        motor_proc.attach(audio_proc)
        board_proc.attach(audio_proc, motor_proc)

        print('Start To Run...')
        board_proc.start()
        motor_proc.start()
        audio_proc.start()

        audio_proc.join()
        motor_proc.join()
        board_proc.join()

main()