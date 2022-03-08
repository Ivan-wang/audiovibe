# 3/7/22
# Fei Tao
# taofei@feathervibe.com
import numpy as np
from runutils import base_arg_parser,import_module_from_file, print_module
from runutils import _main
import sys
import mappings
import os
from vib_music.misc import init_vibration_extraction_config


def main():
    p = base_arg_parser()
    opt = p.parse_args()
    print(opt)
    params = import_module_from_file("params",opt.config)
    print_module(params)
    librosa_config = None
    plot_config = None
    if opt.task == 'run' or 'build':
        print('Buidling Feature Database...', end='')
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = opt.audio
        librosa_config['len_hop'] = params.len_hop
        librosa_config['stgs'][opt.audmode] = {
            'len_window': params.len_window,
        }

    if opt.plot:
        plot_config = {
            'plots': ['waveform', 'wavermse', 'vibration_adc']
        }

    vib_kwargs_dict = {"duty": params.duty, "recep_field": params.recep_field, "vib_freq":params.vib_freq,
                       "vib_scale":params.vib_scale, "len_window":params.len_window, "split_aud":params.split_aud,
                       "vib_frame_len":params.vib_frame_len}
    _main(opt, opt.vibmode, 'adc', librosa_config, plot_config, vib_kwargs_dict)


### debug part ###
curr_path = os.getcwd()
sys.argv = ["demo.py", "--audio", str(os.path.join(curr_path,"../audio/m1_22k.wav")), "--task", "run"]
print("DEBUG...")
######

main()
