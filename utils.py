import librosa

def load_audio():
    audio, sr = librosa.load('audio/YellowRiverSliced.wav', sr=None)

    return audio, sr

def get_feature(features, k=None, prefix=None):
    if k is not None and k in features:
        return features[k]
    
    for name in features:
        if name.startswith(prefix):
            return features[name]

    return None 

if __name__ == '__main__':
    sound, sr = load_audio()
    print(f'Audio Sample Data Shape {sound.shape}')
    print(f'Audio Sample Rate {sr}')