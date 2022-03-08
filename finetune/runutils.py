import os
import sys

from numpy import double
sys.path.append('..')
import re
import argparse
from pathlib import Path
from typing import Union
from importlib.util import spec_from_file_location, module_from_spec


def import_module_from_file(name, path):
    """Programmatically returns a module object from a filepath"""
    if not Path(path).exists():
        raise FileNotFoundError('"%s" doesn\'t exist!' % path)
    spec = spec_from_file_location(name, path)
    if spec is None:
        raise ValueError('could not load module from "%s"' % path)
    m = module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def print_module(module):
    for o in dir(module):
        if not re.search("__.*", o):
            print(o,"\t",getattr(module, o))


def base_arg_parser():
    p = argparse.ArgumentParser(conflict_handler='resolve')
    p.add_argument('--audio', type=str)
    p.add_argument('--task', type=str, default='run', choices=['run', 'build', 'play'])
    p.add_argument('--data-dir', type=str, default='.')
    p.add_argument('--config', type=str, default="./configs/band_split_demo.py")
    p.add_argument('--plot', action='store_true')
    p.add_argument('--vibmode', type=str, default="band_split")
    p.add_argument('--audmode', type=str, default="melspec")
    return p

def tune_melspec_parser(base_parser=None):
    p = base_arg_parser() if base_parser is None else base_parser
    p.add_argument('--len-window', type=int, default=2048)
    p.add_argument('--n-mels', type=int, default=128)
    p.add_argument('--fmax', type=int, default=-1)

    return p

def tune_rmse_parser(base_parser=None):
    p = base_arg_parser() if base_parser is None else base_parser
    p.add_argument('--len-window', type=int, default=2048)

    return p

def tune_beat_parser(base_parser=None):
    p = base_arg_parser() if base_parser is None else base_parser

    p.add_argument('--len-frame', type=int, default=300)
    p.add_argument('--min-tempo', type=int, default=150)
    p.add_argument('--max-tempo', type=int, default=400)

    return p

def tune_pitch_parser(base_parser=None):
    p = base_arg_parser() if base_parser is None else base_parser

    p.add_argument('--pitch', action='store_true')
    p.add_argument('--pitch-alg', type=str, default='pyin', choices=['pyin', 'yin'])
    p.add_argument('--chroma', action='store_true')
    p.add_argument('--chroma-alg', type=str, default='stft', choices=['stft', 'cqt'])
    p.add_argument('--len-window', type=int, default=2048)
    p.add_argument('--fmin', type=str, default='C2')
    p.add_argument('--fmax', type=str, default='C7')
    p.add_argument('--n-chroma', type=int, default=12)
    p.add_argument('--tuning', type=double, default=0.0)
    p.add_argument('--yin-thres', type=float, default=0.8)

    return p

from vib_music import FeatureExtractionManager
from vib_music import launch_vibration
from vib_music import launch_plotting

def _main(opt, mode, driver, librosa_cfg, plot_cfg, vib_kwargs_dict):
    if opt.task == 'run' or opt.task == 'build':
        ctx = FeatureExtractionManager.from_config(librosa_cfg)
        ctx.save_features(root=opt.data_dir)

    feature_folder = os.path.basename(opt.audio).split('.')[0]
    feature_folder = os.path.join(opt.data_dir, feature_folder)
    if opt.plot and plot_cfg is not None:
        launch_plotting(opt.audio, feature_folder, mode, plot_cfg['plots'])

    if opt.task == 'run' or opt.task == 'play':
        launch_vibration(opt.audio, feature_folder, mode, driver, vib_kwargs_dict)
