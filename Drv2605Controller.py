import time
import timeit
import board
import busio
from datetime import datetime, timedelta
import os
import adafruit_drv2605

def drvAction(timeToGo,ampValue,feqValue):
    end_time = datetime.now() + timedelta(seconds=timeToGo)
    # Set real-time play mode
    drv._write_u8(0x01, 5) 
    # Set real-time play value (amplitude)
    drv._write_u8(0x02, ampValue) 
    # Set real-time play value (frequency)
    drv._write_u8(0x20, feqValue) 
    while datetime.now() < end_time:
        drv.play()
    
def drvClear():
    # Set idol mode
    drv._write_u8(0x01,0)


# Initialize I2C bus and DRV2605 module.
i2c = busio.I2C(board.SCL, board.SDA)
drv = adafruit_drv2605.DRV2605(i2c)
# Enable LRA Open Loop Mode
drv._write_u8(0x1D,0xA1)
# Set Vibration Time in seconds
vibTime = 1
# Set Vibration Amplitude in 0 - 256
vibAmp = 100
# Set Vibration Frequency in 0 - 128 (the larger value the slower freq.)
vibFeq = 128
# Test
drvAction(vibTime, vibAmp, vibFeq)
# Stop Vib
drvClear()
