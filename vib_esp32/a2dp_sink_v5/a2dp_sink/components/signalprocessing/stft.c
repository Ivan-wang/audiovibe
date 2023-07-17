#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "stft.h"
#include "array2d.h"
// #include "config.h"

const element_t FFT_FREQ_128_22050[65] = {0.0, 172.265625, 344.53125, 516.796875,
    689.0625, 861.328125, 1033.59375, 1205.859375, 1378.125, 1550.390625,
    1722.65625, 1894.921875, 2067.1875, 2239.453125, 2411.71875, 2583.984375,
    2756.25, 2928.515625, 3100.78125, 3273.046875, 3445.3125, 3617.578125,
    3789.84375, 3962.109375, 4134.375, 4306.640625, 4478.90625, 4651.171875,
    4823.4375, 4995.703125, 5167.96875, 5340.234375, 5512.5, 5684.765625,
    5857.03125, 6029.296875, 6201.5625, 6373.828125, 6546.09375, 6718.359375,
    6890.625, 7062.890625, 7235.15625, 7407.421875, 7579.6875, 7751.953125,
    7924.21875, 8096.484375, 8268.75, 8441.015625, 8613.28125, 8785.546875,
    8957.8125, 9130.078125, 9302.34375, 9474.609375, 9646.875, 9819.140625,
    9991.40625, 10163.671875, 10335.9375, 10508.203125, 10680.46875, 10852.734375, 11025.0};

// utils
void fft_freq(element_t *freq, int fft_len, float d) {
    float val = 1 / ((float)fft_len * d);
    int N = (fft_len-1) / 2 + 1;
    for (int i = 1; i < N-1; ++i) {
        freq[i] = (float)i * val;
    }
    for (int i = N; i < fft_len; ++i) {
        freq[i] = -(fft_len/2+N-i) * val;
    }
}

void shift_stft_buffer(stft_handler_t *stft, int len, const element_t *data) {
    int shift_len = stft->fft->size - len; // assert shift_len > 0;

    memcpy(stft->raw, stft->raw+len, shift_len*sizeof(element_t));
    if (data == NULL) {
        memset(stft->raw+shift_len, 0, len*sizeof(element_t));
    }
    else {
        memcpy(stft->raw+shift_len, data, len*sizeof(element_t));
    }
}

void windowing_stft_buffer(stft_handler_t *stft) {
    if (stft->hann == NULL) {
        for (int i = 0; i < stft->fft->size; ++i) {
            stft->window[i<<1] = stft->raw[i];
            stft->window[(i<<1)+1] = 0.;
        }
    }
    else {
        for (int i = 0; i < stft->fft->size; ++i) {
            stft->window[i<<1] = stft->hann[i] * stft->raw[i];
            stft->window[(i<<1)+1] = 0.;
        }
    }
}

stft_handler_t *create_stft(int fft_len, int frame_len, int hop_len) {
    stft_handler_t *stft = (stft_handler_t *)malloc(sizeof(stft_handler_t));

    stft->frame_len = frame_len;
    stft->hop_len = hop_len;

    stft->fft = fft_init(fft_len, FFT_COMPLEX, FFT_FORWARD, NULL, NULL);
    stft->window = stft->fft->input; // buffer is 2x of fft len
    stft->raw = (element_t *)malloc(sizeof(element_t)*fft_len);
    stft->spectrum = create_array2d(frame_len, fft_len, NULL); // time x freq
    stft->hann = (element_t *)malloc(sizeof(element_t)*fft_len);

    // hann window
    // use "fft_len" (not "fft_len-1") for periodic window
    for (int i = 0; i < fft_len; ++i) {
        stft->hann[i] = 0.5 * (1. - cosf(M_PI*2*i / (element_t)fft_len));
    }

    // clear data
    array2d_fill(stft->spectrum, 0.);

    return stft;
}

// 1. shift buffer; shift spectrum
// 2. exec fft
// 3. update spectrum
void destroy_stft(stft_handler_t *handler) {
    if (handler == NULL) { return; }
    if (handler->fft != NULL) { fft_destroy(handler->fft); }
    if (handler->hann != NULL) { free(handler->hann);}
    if (handler->raw!= NULL) { free(handler->raw); }
    if (handler->spectrum != NULL) { destroy_array2d(handler->spectrum); }
    // if (handler->window != NULL) { free(handler->window); }
    free(handler);
}

void stft_exec(stft_handler_t *stft, const element_t *raw) {
    // prepare input
    shift_stft_buffer(stft, stft->hop_len, raw);
    windowing_stft_buffer(stft);
    // run fft
    fft_execute(stft->fft);

    // prepare output
    array2d_shift(stft->spectrum, 1, ARRAY_2D_DIM0);
    for (int i = 0; i < stft->fft->size; ++i) {
        stft->spectrum->data[stft->frame_len-1][i] = stft->fft->output[i<<1];
    }
}

// create stft using configuration
// stft_handler_t *init_stft() {
//     return create_stft(CFG_STFT_LEN, CFG_STFT_FRAME_NUM, CFG_STFT_HOP_LEN);
// }