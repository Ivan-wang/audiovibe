#include <stdlib.h>
#include "filter.h"
#include "hrps.h"
#include "config.h"

extern const int CFG_STFT_LEN;
extern const int CFG_STFT_FRAME_NUM;

// utils
// ceil(sec * fs / hop_len)
int sec_to_frame(float sec, int sr, int hop_len) {
    return (int)(sec * sr + hop_len - 1) / hop_len;
}

// ceil(hz * fft_len / fs)
int hz_to_bin_count(float hz, int sr, int fft_len) {
    return (int)(hz*fft_len + sr - 1) / sr;
}


// spec shape: frame_len x fft_len
hrps_handler_t *create_hrps(int h_spec, int w_spec, int hfilter_len, int pfilter_len, float beta) {
    // make kernel length odd
    hfilter_len = hfilter_len | 0x1;
    pfilter_len = pfilter_len | 0x1; 
    hrps_handler_t *hrps = (hrps_handler_t *)malloc(sizeof(hrps_handler_t));

    hrps->hormonic = create_array2d(h_spec, w_spec, NULL);
    hrps->percussive = create_array2d(h_spec, w_spec, NULL);
    hrps->residual = create_array2d(h_spec, w_spec, NULL);

    hrps->pwr = create_array2d(h_spec, w_spec, NULL);
    hrps->hbuffer = create_array2d(h_spec, w_spec, NULL);
    hrps->pbuffer = create_array2d(h_spec, w_spec, NULL);

    hrps->hfilter = create_filter1d(h_spec, hfilter_len, FILTER_PAD_ZERO); // filter on time dim (DIM0)
    hrps->pfilter = create_filter1d(w_spec, pfilter_len, FILTER_PAD_ZERO); // filter on freq dim (DIM1)
    hrps->beta = beta;

    return hrps;
}

hrps_handler_t *create_hrps_from_args(hrps_args_t *args) {
    return create_hrps(args->h_spec, args->w_spec, args->hfilter_len, args->pfilter_len, args->beta);
}

hrps_handler_t *create_hrps_from_stft(float sec, float hz, int sr, const stft_handler_t* stft, float beta) {
    int hfilter_len = sec_to_frame(sec, sr, stft->hop_len);
    int pfilter_len = hz_to_bin_count(hz, sr, stft->fft->size);

    return create_hrps(stft->spectrum->dim0, stft->spectrum->dim1, hfilter_len, pfilter_len, beta);
}

void destroy_hrps(hrps_handler_t *hrps) {
    destroy_array2d(hrps->pwr);
    destroy_array2d(hrps->hormonic);
    destroy_array2d(hrps->percussive);
    destroy_array2d(hrps->residual);
    destroy_array2d(hrps->hbuffer);
    destroy_array2d(hrps->pbuffer);

    destroy_filter1d(hrps->hfilter);
    destroy_filter1d(hrps->pfilter);
    free(hrps);
}

void exec_hrps(hrps_handler_t *hrps, const array2d_t* spec) {
    array2d_square(hrps->pwr, spec);

    medfilter_one_dim(hrps->hbuffer, hrps->pwr, hrps->hfilter, ARRAY_2D_DIM0);
    medfilter_one_dim(hrps->pbuffer, hrps->pwr, hrps->pfilter, ARRAY_2D_DIM1);

    array2d_fill(hrps->percussive, 0.);
    array2d_fill(hrps->hormonic, 0.);
    array2d_fill(hrps->residual, 0.);

    for (int dim0 = 0; dim0 < spec->dim0; ++dim0) {
        for (int dim1 = 0; dim1 < spec->dim1; ++dim1) {
            if (hrps->hbuffer->data[dim0][dim1] >= hrps->beta * hrps->pbuffer->data[dim0][dim1]) {
                hrps->hormonic->data[dim0][dim1] = hrps->pwr->data[dim0][dim1];
            }
            else if (hrps->pbuffer->data[dim0][dim1] > hrps->beta * hrps->hbuffer->data[dim0][dim1]) {
                hrps->percussive->data[dim0][dim1] = hrps->pwr->data[dim0][dim1];
            }
            else {
                hrps->residual->data[dim0][dim1] = hrps->pwr->data[dim0][dim1];
            }
        }
    }
}


// create hrps handler using predetermin configuration
hrps_handler_t *init_hrps(int hfilter_len, int pfilter_len, float beta) {
    return create_hrps(CFG_STFT_FRAME_NUM, CFG_STFT_LEN, hfilter_len, pfilter_len, beta);
}