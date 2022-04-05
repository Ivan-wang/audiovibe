import sys
from multiprocessing import Queue
sys.path.append('..')

from vib_music import FeatureBuilder

audio = '../audio/test_beat_short_1.wav'
sr = None
len_hop = 512

fbuilder = FeatureBuilder(audio, sr, len_hop)

recipe = {
    'rmse': {'len_window': 1024}
}

fb = fbuilder.build_features(recipe)

fb.save('./test_fb')
