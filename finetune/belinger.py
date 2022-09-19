# version: 清歌v0.3.soc
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

    # preprocess streaming parameters
    stream_flag = bool(vib_kwargs_dict.get("streaming", False))
    if stream_flag:
        # adujst read audio length
        design_read_audio_len = float(vib_kwargs_dict.get("audio_len", 0.1)) * librosa_config["sr"]
        design_audio_frames = design_read_audio_len % librosa_config["len_hop"]
        assert librosa_config["len_window"] - librosa_config["len_hop"] >=0, "[ERROR] len_window must be larger or equal to len_hop"
        # compute practical read audio length
        practical_read_audio_len = librosa_config["len_hop"] * design_audio_frames    # we use the simplest way by now
        # TODO use more accurate way - add the remaining window
        # practical_read_audio_len = librosa_config["len_hop"] * design_audio_frames + librosa_config["len_window"] - librosa_config["len_hop"]
        vib_kwargs_dict["audio_len"] = practical_read_audio_len

    _main(opt, opt.vibmode, 'adc', librosa_config, plot_config, vib_kwargs_dict)


### debug part ###
curr_path = os.getcwd()

# freqeuncy modulation
# sys.argv = ["belinger.py", "--audio", str(os.path.join(curr_path,"../audio/m1_22k.wav")), "--task", "run",
#             "--vibmode", "rmse_freqmodul", "--audmode", "rmse", "--config", "configs/rmse_freqmodul_demo.py"]

# # qingge 
sys.argv = ["belinger.py", "--audio", str(os.path.join(curr_path,"../audio/m1_cut_22k.wav")), "--task", "run",
            "--vibmode", "band_select_fast", "--audmode", "stft", "--config", "configs/band_select_fast_demo.py"]
print("DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!DEBUG!")
# ######

print("==================================")
print("    萦歌项目   系统：清歌 v0.3.soc   ")
print("==================================")
main()
