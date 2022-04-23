from cmath import log
import numpy as np
from math import log, sqrt
import matplotlib.pyplot as plt
import librosa
from scipy.signal import argrelextrema
from scipy.stats import zscore
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

# bn = 255

# bins = np.linspace(0., 1., bn, endpoint=True)
# mu_bins = [x*(log(1+bn*x)/log(1+bn)) for x in bins]
# sqrt_bins = [sqrt(x) for x in bins]
# plt.figure()
# plt.plot(bins, bins, "b-")
# plt.plot(bins, mu_bins, "r-")
# plt.plot(bins, sqrt_bins, "y-")
# plt.savefig("mu_law.png")
# print("hello")

y, sr = librosa.load("../audio/kick_22k.wav", mono=True)
y_stft = librosa.stft(y, n_fft=512, hop_length=256)

S, phase = librosa.magphase(y_stft)
D = np.abs(y_stft)

oenv = librosa.onset.onset_strength(S=D)
onset_t = librosa.onset.onset_detect(y=y, sr=sr, units="frames", hop_length=256, backtrack=False)
spec_cent = librosa.feature.spectral_centroid(S=S)

oenv_min = argrelextrema(oenv, np.less)[0]
feat = np.zeros((2, len(onset_t)))
for i in range(len(onset_t)):
    feat[0, i] = spec_cent[0, onset_t[i]]
    cands = onset_t[i] - oenv_min
    cands[cands<0] = 99999
    bt_ind = np.argmin(cands)
    bt = oenv_min[bt_ind]
    t = onset_t[i]
    feat[1, i] = t - bt

feat_norm = zscore(feat, axis=1).transpose()
# onset_bt = librosa.onset.onset_backtrack(onset_raw, oenv)

ss = []
for i in range(1, 10):
    gmm = GaussianMixture(n_components=i, random_state=0).fit(feat_norm)
    bic = gmm.bic(feat_norm)
    # curr_ss = silhouette_score(feat_norm, x_label, random_state=0)
    ss.append(bic)

print("hello")