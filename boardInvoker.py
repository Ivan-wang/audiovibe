import os
import numpy as np
from abc import ABC, abstractmethod

# adafruit lib
# import board
# import busio
# import adafruit_drv2605

# dispatch vibration 
class BoardInvoker(object):
    motor_t = {}
    def __init__(self, motors=[]):
        super(BoardInvoker, self).__init__()
        # self.drv = None
        self.motor_cfgs = motors
        self.motors = self._init_motors()

    def _init_motors(self):
        motors = []
        for name, args in self.motor_cfgs:
            if name in BoardInvoker.motor_t:
                motors.append(BoardInvoker.motor_t[name](*args))
            else:
                print(f'Unrecongnized Motor Type {name}')
            
        return motors

    def on_start(self):
        for m in self.motors:
            m.on_start()

    def dispatch(self, vibrations):
        for k in vibrations:
            for m in self.motors:
                if k.startswith(m.vibration_t):
                    m.on_update(self, vibrations[k])

        for m in self.motors:
            m.on_running()

    def on_end(self):
        for m in self.motors:
            m.on_end()

class MotorMeta(type):
    def __new__(cls, clsname, bases, attrs):
        newclass = super(MotorMeta, cls).__new__(cls, clsname, bases, attrs)   
        alias = getattr(newclass, 'alias', None)    
        if alias is not None:
            BoardInvoker.motor_t.update({alias: newclass})
        return newclass

class Motor(object, metaclass=MotorMeta):
    def __init__(self, vibration_t):
        super().__init__()
        self.vibration_t = vibration_t

    @abstractmethod
    def on_start(self):
        pass

    @abstractmethod
    def on_update(self, vibration):
        pass

    @abstractmethod
    def on_running(self):
        pass
    
    @abstractmethod
    def on_end(self):
        pass

class ConsoleSimulationMotor(Motor):
    alias = 'console'
    def __init__(self, vibration_t):
        super().__init__(vibration_t)
        self.buf = None

    def on_start(self):
        return super().on_start()
    
    def on_update(self, vibration):
        self.buf = vibration

    def on_running(self, features):
        print(self.buf)
    
    def on_end(self):
        return super().on_end()

# class Drv2605Motor(Motor):
#     def on_start(self):
#         pass
#         # i2c = busio.I2C(board.SCL, board.SDA)
#         # self.drv = adafruit_drv2605(i2c)

#     def on_running(self, features):
#         return super().on_running(features)
    
#     def on_end(self):
#         return super().on_end()

# class PlotSimulationMotor(Motor):
#     def on_start(self):
#         return super().on_start()
    
#     def on_running(self, features):
#         return super().on_running(features)
    
#     def on_end(self):
#         return super().on_end()

if __name__ == '__main__':
    print(BoardInvoker.motor_t)
    bid = BoardInvoker([('console', ['rmse'])])
    print(bid.motors)
