import os
import sys

# for typing
import argparse
from typing import List, Optional
from argparse import Namespace
from multiprocessing import Process

sys.path.append('..')

def _base_arg_parser():
    p = argparse.ArgumentParser(conflict_handler='resolve')
    p.add_argument('--audio', type=str)
    p.add_argument('--task', type=str, default='run', choices=['run', 'build', 'play'])
    p.add_argument('--len-hop', type=int, default=512)
    p.add_argument('--len-hop-vib', type=int, default=24)
    p.add_argument('--vib-mode', type=str, default='rmse_mode')

    return p

def tune_melspec_parser(base_parser=None):
    p = _base_arg_parser() if base_parser is None else base_parser
    p.add_argument('--len-window', type=int, default=2048)
    p.add_argument('--n-mels', type=int, default=128)
    p.add_argument('--fmax', type=int, default=-1)

    return p

def tune_rmse_parser(base_parser=None):
    p = _base_arg_parser() if base_parser is None else base_parser
    p.add_argument('--len-window', type=int, default=1024)

    return p

from vib_music import FeatureBuilder
from vib_music import AudioFeatureBundle

def _init_features(audio:str, len_hop:int, recipes:Optional[dict]=None) -> AudioFeatureBundle:
    # save features to data dir
    audio_name = os.path.basename(audio).split('.')[0]
    os.makedirs('../data', exist_ok=True)
    os.makedirs(f'../data/{audio_name}', exist_ok=True)

    if recipes is None:
        fb = AudioFeatureBundle.from_folder(f'../data/{audio_name}')
    else:
        fbuilder = FeatureBuilder(audio, None, len_hop)
        fb = fbuilder.build_features(recipes)
        fb.save(f'../data/{audio_name}')

    return fb

from vib_music import get_audio_process
from vib_music import VibrationStream, PCF8591Driver, StreamHandler
from vib_music import LogDriver
from vib_music import VibrationProcess

def _init_processes(audio:str, len_hop:int,
    fb:AudioFeatureBundle, len_vib_frame:int, mode:str='rmse_mode') -> List[Process]:
    sdata = VibrationStream.from_feature_bundle(fb, len_vib_frame, mode)
    sdriver = PCF8591Driver()
    # sdriver = LogDriver()
    shandler = StreamHandler(sdata, sdriver)
    vib_proc = VibrationProcess(shandler)
    
    music_proc = get_audio_process(audio, len_hop)

    return [music_proc, vib_proc]

from vib_editor import launch_vibration
def _main(opt:Namespace, feat_recipes:Optional[dict]=None) -> None:
    fb = _init_features(opt.audio, opt.len_hop, feat_recipes)

    if opt.task == 'run' or opt.task == 'play':
        procs = _init_processes(opt.audio, opt.len_hop, fb, 
            opt.len_hop_vib, opt.vib_mode)
        # master = None -> run vibration in an independent window
        launch_vibration(master=None, process=procs)
