#include "bt_sig_proc.h"


static audio_handler_t *sig_proc_handler = NULL;

void init_audio_handler(audio_handler_t* handler) {
    sig_proc_handler = (audio_handler_t *)malloc(sizeof(audio_handler_t));

    int FFT_LEN = 128; // FFT len for one frame
    int FFT_FRAME_LEN = 8; // buffer 8 frame data
    int HOP_LEN = 64;
    handler->stft_handler = create_stft(FFT_LEN, FFT_FRAME_LEN, HOP_LEN); // spec -> time x freq

    int PFILTER_LEN = 3; // FREQ domain
    int HFILTER_LEN = 5; // TIME domain
    float beta = 2.0;
    // handler->hrps_handler = create_hrps(FFT_FRAME_LEN, FFT_LEN, HFILTER_LEN, PFILTER_LEN, beta);

    int RELATIVETH = 4;
    int GLOBALTH = 20;
    int FILTER_LEN = 19;
    hrps_args_t args = {FFT_FRAME_LEN, FFT_LEN, HFILTER_LEN, PFILTER_LEN, beta};
    handler->peak_handler = create_peak_handler(FFT_FRAME_LEN, FFT_LEN, FILTER_LEN, RELATIVETH, GLOBALTH, &args);

    // return handler;
}

void proc_audio_frame(element_t* frame) {
    stft_exec(sig_proc_handler->stft_handler, frame);
    // exec_hrps(handler->hrps_handler, handler->stft_handler->spectrum);
    extract_peaks(sig_proc_handler->peak_handler, sig_proc_handler->stft_handler->spectrum);
}

void deinit_audio_handler() {
    destroy_stft(sig_proc_handler->stft_handler);
    // destroy_hrps(handler->hrps_handler);
    destroy_peak_handler(sig_proc_handler->peak_handler);

    free(sig_proc_handler);
    sig_proc_handler = NULL;
}


