import yaml

from librosaContext import LibrosaContext
def list_librosa_context():
    ks = list(LibrosaContext.stg_funcs.keys())
    meta_ks = list(LibrosaContext.stg_meta_funcs.keys())

    print(f'Available Librosa Strategies : {ks}')
    print(f'Available Librosa Meta Strategies : {meta_ks}')

from vibrationEncoder import VibrationEncoder
def list_vibration_encoder():
    ks = list(VibrationEncoder.enc_funcs)

    print(f'Available Vibration Encoder Strategies : {ks}')

from matplotlibInvoker import MatplotlibInvoker
def list_matplotlib_invoker():
    ks = list(MatplotlibInvoker.commands)

    print(f'Available Matplotlib Invoker Strategies : {ks}')

from boardInvoker import BoardInvoker
def list_matplotlib_invoker():
    ks = list(BoardInvoker.motor_t)

    print(f'Available Board Motors: {ks}')

from pprint import pprint
def demo_config(save=None):
    config = {}

    if save is not None:
        with open(save, 'wb') as f:
            yaml.dump(config, f)

if __name__ == '__main__':
    list_librosa_context()
    list_vibration_encoder()
    list_matplotlib_invoker()