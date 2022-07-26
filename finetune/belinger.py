# version: 清歌v0.1
# Fei Tao
# taofei@feathervibe.com
import numpy as np
from runutils import base_arg_parser,import_module_from_file, print_params_module, dictize_params_module, \
    delattr_params_module, _main
import sys
import mappings
import os
from vib_music.misc import init_vibration_extraction_config


def main():
    p = base_arg_parser()
    opt = p.parse_args()
    print(opt)
    params = import_module_from_file("params",opt.config)
    # print_params_module(params)
    librosa_config = None
    plot_config = None

    # save configs for vibration
    vib_kwargs_dict, exclude_list = dictize_params_module(params, start_keyword="vib__")

    # save configs for audio
    if opt.task == 'run' or 'build':
        # print('Buidling Feature Database...', end='')
        librosa_config = init_vibration_extraction_config()
        librosa_config['audio'] = opt.audio
        librosa_config['len_hop'] = params.len_hop
        exclude_list.append('len_hop')
        audmode_list = opt.audmode.split(",")
        for a in audmode_list:
            librosa_config['stgs'][a], _ = dictize_params_module(params, exclude_list=exclude_list)

    if opt.plot:
        plot_config = {
            'plots': ['waveform', 'wavermse', 'vibration_adc']
        }
    _main(opt, opt.vibmode, 'adc', librosa_config, plot_config, vib_kwargs_dict)


### debug part ###
curr_path = os.getcwd()
sys.argv = ["demo.py", "--audio", str(os.path.join(curr_path,"../audio/m1_22k.wav")), "--task", "run",
            "--vibmode", "rmse_freqmodul", "--audmode", "rmse", "--config", "configs/rmse_freqmodul_demo.py"]
# sys.argv = ["belinger.py", "--audio", str(os.path.join(curr_path,"../audio/kick_22k.wav")), "--task", "run",
#             "--vibmode", "band_select", "--audmode", "melspec,stft", "--config", "configs/band_select_demo.py"]
print("DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!")
######

print("==================================")
print("    萦歌项目   系统：临时 v1.x       ")
print("==================================")
main()