---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
backgroundImage: url('https://marp.app/assets/hero-background.jpg')
marp: true
---

# How to run and debug project

---
## To run the project
1. Generate Config Template
    1.1 Generate Configure for Feature Extraction
        use `example_vibration_extracton_config()` in `config.py`
    1.2 Generate Configure for Board Invoker
        use `example_board_invoker_config()` in `config.py`
2. Run Feature Extraction.
    2.1 Change the path to feature extraction configure file (in `librosaContext.py` )
    2.2 Run `python librosaContext.py`
3. Change the path to board invoker configure file and run `main.py`

---
## Locate the Bugs
1. Feature Extraction
    1. Change Parameters in Configure File
    2. Code for Feature extraction $\rightarrow$ `librosaContext.py`
2. Board Vibration
    1. Change Parameters in Configure File
    2. Code for loading features files and converting to vibrations $\rightarrow$ `boardInvoker.py`
    3. Code for sending vibrations to board $\rightarrow$ `motors.py`
---
## Locate the Bugs (cont.)

3. Sync Multiple Processes
    1. Code for the processes $\rightarrow$ `main.py`


---
## Examples
1. Check `librosaContext.py` for how to dynamically change the configure
2. Check `main.py` for how to initialize motors

## UNCOMMENT the board code before start! (see next page)

---
## Uncomment the code in `main.py` to activate the board
```python
    # i2c = busio.I2C(board.SCL, board.SDA) # UNCOMMEND LINE 90-93
    # drv = adafruit_drv2605.DRV2605(i2c)
    # drv._write_u8(0x1D, 0xA1) # enable LRA Open Loop Mode

    self.board_on.set(
    if end: # line 99
        break
    print(amp, freq, end) # comment this line
    # Set real-time play value (amplitude)
    # drv._write_u8(0x02, amp) # UNCOMMENT THIS LINE
    # and the following four lines
```