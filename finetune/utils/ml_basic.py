# machine learning basic functions
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import numpy as np


def extract_clustern(input, class_n=[2, 6]):
    """
    Automaticly determines how many classes there is in the input, based on GMM clustering.
    """
    scaler = StandardScaler()
    feat_norm = scaler.fit_transform(input)
    cluster_num = range(min(class_n), max(class_n)+1)
    scores = np.zeros((cluster_num[-1]-cluster_num[0]+1))
    step_count = 0
    for i in cluster_num:
        # kmeans = KMeans(n_clusters=i, random_state=0, max_iter=100).fit(feat_norm)
        # scores[step_count] = kmeans.inertia_
        # step_count += 1
        gmm = GaussianMixture(n_components=i, random_state=0).fit(feat_norm)
        curr_ss = gmm.bic(feat_norm)
        scores[step_count] = curr_ss
        step_count += 1
    return int(cluster_num[np.argmax(scores)])