# VIB ESP32 Readme

## UPDATE - 05/05/2022

Bluetooth music and vibration beta version done

**Add bluetooth supporting classes**
1. Add `BtleDriver` class to communicate with esp32 board
    * Btle message types
2. Add `PulseAudioDriver` class to handle bluetooth music streaming
    * Hack `PulseAudio` lib
3. Add `BlteStreamHandler` class to mimic block-based vibration data transfer
    * Now a bluetooth communication carries multiple frames
    * Automatic reload frames when pulsing or resuming music

**Add esp32 code (using Arduino IDE)**
1. Add `sketch_ble_demo` for basic bluetooth communication
2. Add `sketch_ble`
    1. Bluetooth communication with raspberry Pi
    2. PWM based on the vibration data
    3. LED demo

**TODO**
Integrate with `vib_editor` components

## UPDATE - 04/26/2022

This folder is for the demo on esp32 embedding system.