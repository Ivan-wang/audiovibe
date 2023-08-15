from typing import List, Optional
import time
import serial
import asyncio

# ser = serial.Serial('/dev/ttyS0', 115200, timeout=0.01)
# # BC    01  52  FF      65      03E8    FF DF
# # HEAD  EN  CH  Voltage Duty    Freq    
# cmd = bytearray.fromhex(f'BC0152FF6503E8AAAAFFDF')

# for _ in range(10):
#     ser.write(cmd)
#     time.sleep(0.001)

# for _ in range(10):
#     print(' '.join([f'{x:02x}' for x in ser.read(7)]).upper())
#     time.sleep(0.1)

# ser.close()
# exit(0)

LAST_CMD = ''
CHANNEL_MAP = {'Z': 0b01, '0': 0b00, '1': 0b10}

def check_current(ser:serial.Serial):
    bytes = ser.read(7)
    # CH1, CH2, CH3, CH4 = bytes[1:5]
    print(' '.join([f'{x:02x}' for x in bytes]).upper())
    print('Channel Current (0 - 255):', 'mA '.join([f'{int(x)/255*16:.2f}' for x in bytes[1:5]]))

def set_configs(ser:serial.Serial, cmd:str, last_cmd:Optional[str]=None):
    if len(cmd) == 0:
        print('Repeat last command...', last_cmd)
        if last_cmd is not None:
            cmd_hex = last_cmd
        else:
            return
    else:
        ch1, ch2, ch3, ch4, volt, freq, duty = cmd.rstrip().split(' ')
        channels = list([x.upper() for x in reversed([ch1, ch2, ch3, ch4])])

        # must have a GND unless all ZZ
        if all([x == 'Z' for x in channels]):
            bytes = bytearray.fromhex('BC0100000000000000AAAAFFDF')
            ser.write(bytes)
            return

        if any([x != 'Z' for x in channels]) and all([x != '0' for x in channels]):
            raise ValueError('Must have one GND unless all channels are ZZ')
        if any([x not in CHANNEL_MAP for x in channels]):
            raise ValueError('Channel value must be in (0,1,Z)')

        channel_controls = 0
        for c in channels:
            channel_controls = (channel_controls << 2) | CHANNEL_MAP[c]

        volt = int(volt)
        if volt < 0 or volt > 255:
            raise ValueError('Voltage out of range [0, 255]')
        duty = int(duty)
        if duty < 0 or duty > 100:
            raise ValueError('Duty out of range [0, 100]')
        cmd_hex = f'BC01{channel_controls:02X}{int(volt):02X}{duty*2+1:02X}{int(freq):04X}AFAAFFDF'
        print(cmd_hex)

    bytes = bytearray.fromhex(cmd_hex)
    # for _ in range(5):
    ser.write(bytes)
    # ser.flush()
    time.sleep(0.001)
    # for _ in range(5):
    check_current(ser)

    return cmd_hex

def main():
    print("Format: <CH1> <CH2> <CH3> <CH4> <Voltage> <FREQ> <DUTY>")
    print("Range: <CH1-4> 0|1|Z; <Voltage> 0-255; <FREQ> 1-65536; <DUTY> 0-100;")
    print("Press ENTER to REPEAT last command, Use Ctrl+C to exit")

    ser = serial.Serial('/dev/ttyS0', 115200, timeout=0.01)
    time.sleep(0.1)
    last_cmd = ''

    while True:
        try:
            cmd = input("[CMD] ")
        except KeyboardInterrupt:
            set_configs(ser, 'Z Z Z Z 0 0 0') # shut down
            ser.close() # close UART
            break

        # if len(cmd) != 0:
            # cmd = f'1 0 Z Z 180 {int(cmd)} 50'

        try:
            last_cmd = set_configs(ser, cmd, last_cmd)
        except Exception as e:
            print('Command Format Error', e)

main()