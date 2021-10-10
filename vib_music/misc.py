import yaml
from collections import OrderedDict

BASE_HOP_LEN = 512

def init_driver_config(save=None):
    config = OrderedDict()
    config['version'] = 0.2
    config['audio'] = None
    config['datadir'] = '.'

    config['motors'] = [
        ('console', {'show_none': False, 'show_frame': True}),
        # other motor
    ]

    config['iter_kwargs'] = {}

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)

    return dict(config)


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

def init_vibration_extraction_config(save=None):
    config = OrderedDict()
    config['version'] = 0.2

    # define common settings
    len_hop = BASE_HOP_LEN
    # audio
    config['audio'] = None
    config['sr'] = None
    config['len_hop'] = len_hop

    # extract vibration
    stgs = {
        # other strategies here
    }
    config['stgs'] = stgs

    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)

    return dict(config)

def example_vibration_extracton_config(save=None):
    config = OrderedDict()
    config['version'] = 0.2

    # define common settings
    len_hop = BASE_HOP_LEN
    # audio
    config['audio'] = None
    config['sr'] = None
    config['len_hop'] = len_hop

    # extract vibration
    stgs = {
        'beatplp': {
            # common args
            'len_frame': 300,
            # other args
            'tempo_min': 150,
            'tempo_max': 400
        }
        # other strategies here
    }
    config['stgs'] = stgs
    if save is not None:
        with open(save, 'w') as f:
            yaml.dump(dict(config), f, sort_keys=False)

    return config

if __name__ == '__main__':
    example_vibration_extracton_config('configs/librosa_context.yaml')