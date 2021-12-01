
AUDIO_RUNTIME_READY = False
try:
    import pyaudio
except ImportError:
    AUDIO_RUNTIME_READY = False
else:
    AUDIO_RUNTIME_READY = True
    from pyaudio import PyAudio

DRV2605_ENV_READY = False
try:
    import board
    import busio
    import adafruit_drv2605
except ImportError:
    pass
else:
    DRV2605_ENV_READY = True

ADC_ENV_READY = False
try:
    import smbus
except ImportError:
    pass
else:
    ADC_ENV_READY = True

