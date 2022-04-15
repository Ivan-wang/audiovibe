from distutils.log import warn
from logging import warning
import warnings
try:
    import pyaudio
except ImportError:
    warnings.warn('PyAudio lib not found')
else:
    from pyaudio import PyAudio

try:
    import smbus
except ImportError:
    warnings.warn('smbus lib not found')


