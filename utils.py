import librosa

def load_audio():
    audio, sr = librosa.load('audio/YellowRiverSliced.wav', sr=None)

    return audio, sr

if __name__ == '__main__':
    sound, sr = load_audio()
    print(f'Audio Sample Data Shape {sound.shape}')
    print(f'Audio Sample Rate {sr}')