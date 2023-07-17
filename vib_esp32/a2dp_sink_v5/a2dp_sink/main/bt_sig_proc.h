#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "array2d.h"
#include "stft.h"
#include "hrps.h"
#include "peak.h"
#include "fft.h"

typedef struct {
    int frame_len;

    stft_handler_t *stft_handler;
    // hrps_handler_t *hrps_handler;
    peak_handler_t *peak_handler; // peak handler contains a hrps handler

} audio_handler_t;

// extern audio_handler_t* sig_proc_handler;

void init_audio_handler();
void proc_audio_frame(element_t* frame);
void deinit_audio_handler();
