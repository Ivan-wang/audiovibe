import os
import numpy as np
from abc import ABC, abstractmethod

class BoardInvoker(object):
    commands = {}
    def __init__(self):
        super().__init__()

    def _on_start(self):
        # init board
        pass
    
    def execute(self, features):
        self._on_start()

class Motor(ABC):
    @abstractmethod
    def run(self, features):
        pass

class Drv2605Motor(Motor):
    def run(self, features):
        pass

class PlotMotor(Motor):
    def run(self, features):
        pass
