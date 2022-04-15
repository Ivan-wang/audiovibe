from utils import tune_rmse_parser
from utils import _main

def main():
    p = tune_rmse_parser()
    opt = p.parse_args()
    print(opt)

    feat_recipes = None
    if opt.task == 'run' or 'build':
        feat_recipes = {}
        feat_recipes['rmse'] = {'len_window': opt.len_window}

    _main(opt, feat_recipes)

main()