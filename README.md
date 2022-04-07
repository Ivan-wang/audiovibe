# Setup
##	1. setup envrionment
###	1.1 For desktop user 
	
	1.1.1 Install miniconda

	1.1.2 create conda enviroment with the command
	   ```bash
	   conda env create -n audio -f conda_requirements.yml
	   ```
	   then activate it by
	   ```bash
	   conda activate audio
	   ```
###	1.2 For raspberry pi user
	
	1.2.1 Create virtual Python environment





 Install `librosa`. (Requires `llvm-lite`)

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
4. Configure environment
   
   ```bash
   pip3 install -r pip_requirements.txt
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
