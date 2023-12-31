# VIB Music ReadMe

## UPDATE - 04/14/2022
1. enhance `FeaturePlotter` to support GUI drawing
    * update all drawing function (`plots.py`)
2. `rmse_mode` is now a standard vibration mode, use it as the baseline
3. refactor data stream
    * add `AudioStream` class for audio data interface
4. Lots of bug fixes

## UPDATE - 04/01/2022
**Refactor `vib_music` lib to support multi-stream vibration and more control signals**
1. add `core` sub-module for core interface class
    * separate `FeatureManager` to `FeatureBundle` and `FeatureBuilder`
    * refactor `PlotManager` as `FeaturePlotter`
    * add `StreamData` as a general data interface
    * add `StreamDriver` as a general hardware interface
    * add `StreamEvent` for control

2. refactor or implement other classes
    * implement `LogDriver`, `AudioDriver`, and `PCF8591Driver` for debugging, music, and vibration
    * refactor feature extraction functions
    * refactor feature plottng functions
    * implement `WaveAudioStream` for .wav file
    * implement `VibrationStream` for vibration data
    * add `StreamHandler` and `AudioStreamHandler` for high level operations, like pulse, resume
    * refactor `StreamProcess` and `VibrationProcess`

3. debuging new `vib_music` module

**TODO**

move all finetune functions to new architecture