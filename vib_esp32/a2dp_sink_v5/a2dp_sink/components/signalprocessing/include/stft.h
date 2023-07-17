#ifndef _STFT_H_
#define _STFT_H_

#include "array2d.h"
#include "fft.h"

// extern const element_t FFT_FREQ_128_22050[65];

typedef struct {
    int frame_len;
    int hop_len;

    element_t *hann;
    element_t *window;
    element_t *raw; // buffering output

    fft_config_t *fft;
    array2d_t *spectrum;
} stft_handler_t;

stft_handler_t *create_stft(int fft_len, int frame_len, int hop_len);
void destroy_stft(stft_handler_t *handler);
void stft_exec(stft_handler_t *stft, const element_t *raw);

// create stft using configuration
stft_handler_t *init_stft();

#endif