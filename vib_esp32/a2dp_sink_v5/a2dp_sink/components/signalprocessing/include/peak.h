#ifndef _PEAK_EXT_H_
#define _PEAK_EXT_H_
#include <math.h>

#include "array2d.h"
#include "filter.h"
#include "hrps.h"
#include "utils.h"

typedef struct {
    int h_spec;
    int w_spec;
    int filter_len;

    int relative_th;
    int globa_th;
} peak_args_t;

typedef struct {
    float relative_th;
    float global_th;

    array2d_t *spec_db;
    array2d_t *peaks;
    filter1d_t *filter;

    array2d_t *buf; // filter buffer
    element_t *reduce_buf;

    hrps_handler_t *hrps_handler;
    argsort_handler_t *argsort_handler;
} peak_handler_t;

peak_handler_t *create_peak_handler(int h_spec, int w_spec, int filter_len, int relative_th, int global_th, hrps_args_t *hrps_args);
peak_handler_t *create_peak_handler_from_args(peak_args_t* peak_args, hrps_args_t *hrps_args_t);
void extract_peaks(peak_handler_t *peaks, const array2d_t *spec);
// void refine_peaks(peak_handler_t *peaks, const array2d_t *harmonic, const array2d_t *percussive, const array2d_t *residual);

void refine_peaks(peak_handler_t *peaks, const array2d_t *linspec, int index);
void destroy_peak_handler(peak_handler_t *peaks);

#endif