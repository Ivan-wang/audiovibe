## 	A. Setup
###	1. setup envrionment
#####	1.1 desktop user (ubuntu)
	
Install miniconda
create conda enviroment with the command
  ```bash
  conda env create -n audio -f conda_requirements.yml
  ```
then ***activate*** it by
  ```bash
  conda activate audio
  ```
#####	1.2 raspberry pi user

Create virtual Python environment
  ```bash
  python3 -m venv audio
  ```
then ***activate*** it by
  ```bash
  source ~/audio/bin/activate
  ```
When the environment is activated, the environment name ("audio") appears in the terminal window like this
`pi@raspberrypi:~$` $\rightarrow$ `(audio)pi@raspberrypi:~$`

###	2. install dependencies
#####	2.1 install llvm and related libraries

Install llvm
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
  export LLVM_CONFIG=/usr/bin/llvm-config-8 
  ```

#####	2.2 configure environment

Install all needed packages by pip
  ```bash
  pip3 install -r pip_requirements.txt
  ```
Check `librosa`
  ```bash
  python -c "import librosa; print(librosa.__version__)" # 0.8.0
  ```

#####	2.3 install pyaudio (for users who have hardware, e.g. raspberry pi)

Install pyaudio and dependencies
  ```bash
  sudo apt-get install python-all-dev portaudio19-dev
  pip3 install pyaudio
  ```
Check Pyaudio
  ```bash
  python -c "import pyaudio; audio = pyaudio.PyAudio()"
  ```
You may see many warnings for "unknown PCM cards". ***Pay attention to this line***
  ```text
  ALSA lib pcm_a52.c:823:(_snd_pcm_a52_open) a52 is only for playback
  ```
If you can see the above line, the installation is success.

####	3. develop and use
Every time when you develop (or use), ***you should firstly activate the envrionment following the commands in section 1. (find the corresponding command for your system)***

##	B. Must-know notes
* developer can use audio/kick_22k.wav (22k hz) or audio/kick.wav (44k hz) as basic audio tracks for development; audio/m1_22k.wav (22k hz) or audio/m1.wav (44k hz) can be used as advanced audio tracks for development

* final vibration signal output to raspberry, should have at least 60 (when 255 is max) amplitude to feel the vibration. when it is low, such as [0, 0, 0, 20, 20, ..., 20, 0, 0, 0], vibration cannot be felt.
