import argparse

def _base_arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('--audio', type=str)
    p.add_argument('--task', type=str, default='run', choices=['run', 'build', 'play'])
    p.add_argument('--len-hop', type=int, default=512)
    p.add_argument('--data-dir', type=str, default='.')

    return p

def tune_beat_parser(base_parser=None):
    if base_parser is None:
        p = _base_arg_parser()

    p.add_argument('--len-frame', type=int, default=300)
    p.add_argument('--min-tempo', type=int, default=150)
    p.add_argument('--max-tempo', type=int, default=400)

    return p

