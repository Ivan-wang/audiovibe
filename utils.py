import librosa

def load_audio():
    audio, sr = librosa.load('audio/YellowRiverSliced.wav', sr=None)

    return audio, sr

if __name__ == '__main__':
    _, sr = load_audio()
    print(f'Audio Sample Rate {sr}')