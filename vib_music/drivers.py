import librosa
from finetune.utils.signal_separation import hrps
from finetune.utils.signal_analysis import remove_harmonics, extract_peaks
from finetune.utils.wave_generator import periodic_rectangle_generator
from finetune.utils.global_paras import PEAK_LIMIT
from math import log
import abc


class VibrationDriver(abc.ABC):
    def __init__(self, vibration_data=None) -> None:
        super(VibrationDriver, self).__init__()
        if vibration_data is None:
            self.vibration_iter = None
            self.vibration_len = 0
        else:
            self.vibration_len = len(vibration_data)
            self.vibration_iter = iter(vibration_data)

        self.device = None
        self.blocking = False

    def __len__(self):
        return self.vibration_len

    @abc.abstractmethod
    def on_start(self):
        return

    @abc.abstractmethod
    def on_running(self, update=False):
        return

    @abc.abstractmethod
    def on_close(self):
        return

from .env import DRV2605_ENV_READY
if DRV2605_ENV_READY:
    import board
    import busio
    import adafruit_drv2605

class DR2605Driver(VibrationDriver):
    def __init__(self, vibrations, wavefile=None, fm=None, **kwargs) -> None:
        if (vibrations.shape[1] != 2):
            vibrations = None
        super().__init__(vibration_data=vibrations)

        self.amp = 0
        self.freq = 0

    def on_start(self):
        if DRV2605_ENV_READY:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.device = adafruit_drv2605.DRV2605(i2c)
            self.device._write_u8(0x1D, 0xA1) # enable LRA Open Loop Mode
            return True
        else:
            return False

    def on_running(self, update=False):
        if update:
            try:
                self.amp, self.freq = next(self.vibration_iter)
            except StopIteration:
                return False
        self.device._write_u8(0x02, self.amp) # Set real-time play value (amplitude)
        self.device._write_u8(0x20, self.freq) # Set real-time play value (frequency)
        self._write_u8(0x01, 5) # Set real-time play mode
        self.device.play()
        return True

    def on_close(self):
        self.device._write_u8(0x01, 0)

from .env import ADC_ENV_READY
if ADC_ENV_READY:
    import smbus

# NOTE: each sample accept at most 8 operations
import numpy as np
class AdcDriver(VibrationDriver):
    def __init__(self, vibration_data=None, wavefile=None, fm=None, **kwargs) -> None:
        if isinstance(vibration_data, np.ndarray):
            if len(vibration_data.shape) > 2:
                print(f'vibration data should be at most 2D but get {vibration_data.shape}')
                vibration_data = None
        else:
            print(f'need a np.ndarray for vibration data but get {type(vibration_data)}')
            vibration_data = None
        super().__init__(vibration_data=vibration_data)

        # self.amp = 0

        # when use a sequence for each frame, set blocking mode as true
        if len(vibration_data.shape) > 2:
            self.blocking = False
        
        self.streaming = kwargs.get("streaming", False)
        if self.streaming:
            assert wavefile is not None, "[ERROR] wavefile must be provided under streaming"
            assert fm is not None, "[ERROR] FeatureManager must be passed under streaming"
        self.wavefile = wavefile
        self.fm = fm

    def on_start(self):
        if self.vibration_iter is None:
            return False

        if ADC_ENV_READY:
            self.device = smbus.SMBus(1)
            return True
        else:
            return False


    def on_running(self, update=False, data=None, params=None):
        # for normal offline data
        if update:
            try:
                # process based on streaming status
                if data is None:
                    amp = next(self.vibration_iter)
                else:
                    # TODO we use fixed feats and algorithms by now, may add options later
                    len_window = params["len_window"]
                    len_hop = params["len_hop"]
                    sr = params["sr"]
                    # feature extraction
                    stft = librosa.stft(data, n_fft=len_window, hop_length=len_hop, win_length=len_window, window='hann',
                                    center=True, pad_mode='constant')
                    stft_freq = librosa.fft_frequencies(sr=sr, n_fft=len_window)
                    linspec = np.abs(stft)**2.0    # power linear spectrogram
                    
                    # select bins lower than 8k hz
                    num_8k_bins = np.sum(stft_freq<=8000)
                    linspec = linspec[:num_8k_bins,:]
                    stft_freq = stft_freq[:num_8k_bins]
                    stft_len_window = len_window

                    feat_dim, feat_time = linspec.shape
                    global_scale = params.get("global_scale", 0.01)
                    hprs_harmonic_filt_len = params.get("hprs_harmonic_filt_len", 0.1)
                    hprs_percusive_filt_len = params.get("hprs_percusive_filt_len", 400 * stft_len_window / 512)    # TODO this is determined by experience
                    hprs_beta = params.get("hprs_beta", 4.0)
                    peak_globalth = params.get("peak_globalth", 20)
                    peak_relativeth = params.get("peak_relativeth", 4)
                    stft_peak_movlen = int(params.get("stft_peak_movlen", 400//np.abs(stft_freq[2]-stft_freq[1])))    # TODO this is determined by experience
                    vib_extremefreq = params.get("vib_extreamfreq", [50,500])
                    peak_limit = params.get("peak_limit", -1)
                    vib_maxbin = params.get("vib_maxbin", 255)
                    vib_bias = params.get("vib_bias", 80)
                    duty = params.get("duty", 0.5)
                    vib_frame_len = params.get("vib_frame_len", 24)

                    assert global_scale>0 and global_scale<=1.0, "global scale must be in (0,1]"


                    # get relationship between vib-freq and audio-freq
                    # we assume they have linear relationship: aud_freq = a * vib_freq + b
                    # TODO we need more sophisticated way to model the relationship
                    a = float((min(stft_freq)-max(stft_freq))) / (min(vib_extremefreq)-max(vib_extremefreq))
                    b = max(stft_freq) - a * max(vib_extremefreq)


                    # harmonic-percusive-residual separation
                    # start_t = time.time()
                    power_spec_h, power_spec_p, power_spec_r, M_h, M_p, M_r = hrps(linspec, sr, len_harmonic_filt=hprs_harmonic_filt_len,
                                                                                len_percusive_filt=hprs_percusive_filt_len, beta=hprs_beta,
                                                                                len_window=stft_len_window, len_hop=len_hop)

                    harm_peaks = extract_peaks(power_spec_h, peak_movlen=stft_peak_movlen, peak_relativeth=peak_relativeth, peak_globalth=peak_globalth)
                    spec_mask = harm_peaks

                    # get top peaks
                    spec_masked = linspec * harm_peaks
                    if peak_limit<=0:
                        # automatically determin peak limit
                        # TODO more sophisticated way to determin peak limits
                        peak_mask = np.zeros_like(spec_mask)
                        power_spec_sum = np.sum(linspec, axis=0)
                        power_spec_h_sum = np.sum(power_spec_h, axis=0)
                        power_spec_p_sum = np.sum(power_spec_p, axis=0)
                        power_spec_r_sum = np.sum(power_spec_r, axis=0)
                        h_ratio = power_spec_h_sum / power_spec_sum
                        p_ratio = power_spec_p_sum / power_spec_sum
                        r_ratio = power_spec_r_sum / power_spec_sum
                        for ti in range(feat_time):
                            if p_ratio[ti]>=2*r_ratio[ti] and p_ratio[ti]>2*h_ratio[ti]:
                                curr_peak_limit = 3
                            elif r_ratio[ti]>2*h_ratio[ti]  and r_ratio[ti]>2*p_ratio[ti]:
                                curr_peak_limit = 2
                            elif h_ratio[ti]>2*p_ratio[ti] and h_ratio[ti]>2*r_ratio[ti]:
                                curr_spec_mask = np.expand_dims(harm_peaks[:, ti], axis=1)
                                curr_spec = np.expand_dims(linspec[:, ti], axis=1)
                                spec_mask_no_harms, curr_spec_mask = remove_harmonics(curr_spec_mask, curr_spec, stft_freq)
                                curr_peak_limit = int(min(PEAK_LIMIT, np.sum(spec_mask_no_harms)+1))
                            else:
                                curr_peak_limit = PEAK_LIMIT
                            peak_inds = spec_masked[:,ti].argsort()[::-1][:curr_peak_limit]
                            peak_mask[peak_inds, ti] = 1
                    else:
                        # given pre-set peak_limit
                        spec_masked = librosa.power_to_db(spec_masked)
                        peak_inds = np.argpartition(spec_masked, -peak_limit, axis=0)[-peak_limit:, :]    # top peaks inds at each time point
                        peak_mask = np.zeros_like(spec_mask)
                        np.put_along_axis(peak_mask, peak_inds, 1, axis=0)    # set 1 to peak mask where top peaks are seleted
                    # incorporate peak's mask
                    spec_masked = spec_masked * peak_mask
                    
                    # generate vibration
                    final_vibration = 0
                    for f in range(feat_dim):    # per mel bin
                        # get vib freq: vib_freq = (aud_freq - b) / a
                        curr_aud_freq = stft_freq[f]
                        curr_vib_freq = round((curr_aud_freq-b)/a)    # we round it for wave generation
                        curr_vib_wav = periodic_rectangle_generator([1,0.], duty=duty, freq=curr_vib_freq, frame_num=feat_time,
                                                                frame_time=len_hop/float(sr), frame_len=vib_frame_len)
                        # get vib magnitude
                        curr_melspec = spec_masked[f, :]
                        curr_vib_mag = np.expand_dims(curr_melspec, axis=1)
                        curr_vib_mag = np.tile(curr_vib_mag, (1, vib_frame_len))    # tile to form a matrix (frame_num, frame_len)
                        # generate curr vib
                        curr_vib = curr_vib_wav * curr_vib_mag
                        # accumulate
                        if f == 0:
                            final_vibration = curr_vib
                        else:
                            final_vibration += curr_vib

                    assert not isinstance(final_vibration,int), "final_vibration is not assigned!"
                    
                    # post-process
                    final_vibration = final_vibration / feat_dim    # average accumulated signal
                    final_max = np.max(final_vibration)
                    final_min = np.min(final_vibration)
                    bin_num = vib_maxbin-vib_bias
                    bins = np.linspace(0., 1., bin_num, endpoint=True)    # linear bins for digitizing
                    mu_bins = [x*(log(1+bin_num*x)/log(1+bin_num)) for x in bins]    # mu-law bins
                    # final normalization
                    final_vibration_norm = (final_vibration - final_min) / (final_max - final_min)
                    # digitize
                    final_vibration_bins = np.digitize(final_vibration_norm, mu_bins)
                    final_vibration_bins = final_vibration_bins.astype(np.uint8)
                    # add offset
                    final_vibration_bins += vib_bias
                    # set zeros (we have to do this for body feeling)
                    global_min = np.min(spec_masked[np.nonzero(spec_masked)])    # find global minimum except 0
                    threshold_val = (PEAK_LIMIT//2) * global_min    # we set zeroing condition: if less than half of {peak_limit} bins have {global_min} values
                    threshold_val_norm = (threshold_val - final_min) / (final_max - final_min)
                    threshold_val_bin = np.digitize(threshold_val_norm, mu_bins)
                    final_vibration_bins[final_vibration_bins<=vib_bias+threshold_val_bin] = 0    # set zeros below threshold

                    # change shape from [nframes x vib_num_per_frame] to [total_vib_num]
                    vib_frames, vib_num_per_frame = final_vibration_bins.shape
                    final_amp = np.reshape(final_vibration_bins, (int(vib_frames*vib_num_per_frame)))

                    amp = final_amp
            except StopIteration:
                return False
            else:
                if isinstance(amp, np.ndarray):
                    for a in amp:
                        self.device.write_byte_data(0x48, 0x40, a)
                else:
                    for _ in range(4):
                        self.device.write_byte_data(0x48, 0x40, amp)
                    self.device.write_byte_data(0x48, 0x40, 0)
        return True

    def on_close(self):
        # close the device?
        return
