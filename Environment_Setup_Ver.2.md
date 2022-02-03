# Environment Setup

1. Create virtual Python environment

   ```bash
   python3 -m audio
   ```

2. Activate Python virtual environment

   ```bash
   source ~/audio/bin/activate
   ```

   When the environment is activated, the environment name ("audio") appears in the terminal window like this

   `pi@raspberrypi:~$` $\rightarrow$ `(audio)pi@raspberrypi:~$`

3. Install Python library

   *when the environment is activate, run `python` is equivalent to run `python3`, and `pip` is equivalent to `pip3`. The following commands will use `python` and `pip`* for simplicity

   ```bash
   pip install matplotlib
   pip install pandas
   pip install pyyaml
   pip install scikit-learn
   pip install tqdm
   pip install wheel
   ```

4. Install `librosa`. (Requires `llvm-lite`)

   Install llvm and related libraries

   ```bash
   sudo apt install libblas-dev llvm-8
   sudo apt-get install libatlas-base-dev
   ```

   Check `llvm-config`

   ```bash
   which llvm-config-8 # /usr/bin/llvm-config-8
   ```

   Set the environment variable `LLVM_CONFIG` and Install `librosa` (as well as other dependency)

   ```bash
   LLVM_CONFIG=/usr/bin/llvm-config-8 pip install llvmlite==0.31.0 numba==0.48.0 colorama==0.3.9 librosa==0.8.0
   ```

   Check `librosa`

   ```bash
   python -c "import librosa; print(librosa.__version__)" # 0.8.0
   ```

   

5. Install pyaudio

   ```bash
   sudo apt-get install python-all-dev portaudio19-dev
   pip3 install pyaudio
   ```

   Check Pyaudio

   ```bash
   python -c "import pyaudio; audio = pyaudio.PyAudio()"
   ```

   You may see many warnings for "unknown PCM cards". Pay attention to this line

   ```text
   ALSA lib pcm_a52.c:823:(_snd_pcm_a52_open) a52 is only for playback
   ```

   If you can see the above line, the installation is success.