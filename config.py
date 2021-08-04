import yaml

from pprint import pprint
from collections import OrderedDict
WIN_LEN = 4096
HOP_LEN = 1024
FRAME_LEN = 300

def example_board_invoker_config(save=None):
    config = OrderedDict()
    config['version'] = 0.2
    config['audio'] = None

    config['motors'] = [
        ('console', {'show_none': False, 'show_frame': True}),
        # other motor
    ]

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)

    return config

def example_vibration_extracton_config(save=None):
    config = OrderedDict()
    config['version'] = 0.2

    # define common settings
    len_hop = HOP_LEN
    len_frame = FRAME_LEN
    # audio
    config['audio'] = None
    config['sr'] = None
    config['len_hop'] = len_hop
    config['len_frame'] = len_frame

    # extract vibration
    stgs = {
        'beatplp': {
            # common args
            'hop': len_hop,
            'len_frame': len_frame,
            # other args
            'tempo_min': 150,
            'tempo_max': 400
        }
        # other strategies here
    }

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)

    return config

def demo_config(save=None):
    config = OrderedDict() # use OrderedDict for easy reading
    config['version'] = 0.1

    # audio
    config['audio'] = None
    config['sr'] = None

    # librosa context config
    strategy = {
        'rmse': {'frame': FRAME_LEN, 'hop': HOP_LEN},
        'pitchyin': {'frame': FRAME_LEN, 'hop': HOP_LEN, 'thres': 0.8},
        'beatplp': {'hop': HOP_LEN, 'num_frame': WIN_LEN}
    }
    
    config['strategy'] = strategy

    # vibration encoder
    vibration_enc = [
        'rmse_level'
    ]
    config['vibration_enc'] = vibration_enc

    # board invoker
    motors = {
        # motor, [features,...]
        'console': ['rmse', 'pitchyin']
    }
    config['motors'] = motors

    pprint(config)

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)
        
    return config

if __name__ == '__main__':
    demo_config('configs/demo.yaml')