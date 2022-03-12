from .FeatureExtractionManager import FeatureExtractionManager
from .FeatureManager import FeatureManager
from .processes import AudioProcess
from .processes import BoardProcess

from .plot import PlotManager

from .drivers import VibrationDriver
from .drivers import DR2605Driver
from .drivers import AdcDriver

from .utils import launch_vibration
from .utils import launch_plotting

from .features import *

from .misc import VIB_FRAME_LEN, BASE_HOP_LEN