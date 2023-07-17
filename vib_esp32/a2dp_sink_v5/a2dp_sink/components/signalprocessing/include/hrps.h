#ifndef _HRPS_H_
#define _HRPS_H_

#include <math.h>
#include "array2d.h"
#include "filter.h"
#include "stft.h"

typedef struct {
    // int k_time;
    // int k_freq;
    
    // float hsec;
    // float phz;
    // float beta;
    int h_spec;
    int w_spec;

    int hfilter_len;
    int pfilter_len;

    float beta;
} hrps_args_t;

typedef struct {
    array2d_t *hormonic;
    array2d_t *percussive;
    array2d_t *residual;

    array2d_t *pwr;
    array2d_t *hbuffer;
    array2d_t *pbuffer;

    filter1d_t *pfilter;
    filter1d_t *hfilter;

    float beta;
} hrps_handler_t;

hrps_handler_t *create_hrps(int h_spec, int w_spec, int hfilter_len, int pfilter_len, float beta);
hrps_handler_t *create_hrps_from_args(hrps_args_t* args);
hrps_handler_t *create_hrps_from_stft(float sec, float hz, int sr, const stft_handler_t* stft, float beta);
void destroy_hrps(hrps_handler_t *handler);
void exec_hrps(hrps_handler_t *hrps, const array2d_t* spec);

// create hrps handler using predetermin configuration
hrps_handler_t *init_hrps(int hfilter_len, int pfilter_len, float beta);

#endif