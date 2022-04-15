# Vib Editor Branch ReadMe

## UPDATE - 04/01/2022
1.  Add `VibPlayWidget` class to support music and vibration control function
    * Basic: Start, Pulse, Resume, and Stop
    * Progress: Forward (10 frames), Backward (10 frames), and Slider Control
2. Add `BackendHelper` class to manage music and vibration processes for GUI
    * Add `SliderHelperThread` to manage playing progress
3. Add `launch_vibration_GUI` function to invork `VibPlayWidget` from processes
4. Refactor `VibTransformQueue` class
5. Migrate previous call to `vib_music`

**TODO**
1. Migrate previous GUI frame to new `vib_music` lib