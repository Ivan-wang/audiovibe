from librosaContext import LibrosaContext
from matplotlibInvoker import MatplotlibInvoker

ctx = LibrosaContext()
# ctx.strategy = ['stempo', 'dtempo', 'gramtempo_512']
ctx.strategy = [
    'rmse_1024_512',
    'pitchyin_2048_512_0.8']

features = ctx.audio_features()
print(list(features.keys()))

mi = MatplotlibInvoker(save_dir='plots')
mi.execture(features)
