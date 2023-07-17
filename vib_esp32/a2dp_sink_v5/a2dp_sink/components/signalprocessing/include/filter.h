#ifndef _FILTER_2D_H_
#define _FILTER_2D_H_

#include "array2d.h"

typedef enum {
    FILTER_PAD_ZERO = 0,
    FILTER_PAD_NEAREST,
    // FILTER_PAD_MIRROR,
    FILTER_PAD_MAX
} filter_padding_t;

// typedef enum {
//     FILTER_2D = 0,
//     FILTER_2D_DIM0,
//     FILTER_2D_DIM1,
//     // FILTER_2D_DIM_SEPARATED,
//     FILTER_MODE_MAX
// } filter2d_mode_t;

// typedef struct {
//     int k0;
//     int k1;
//     filter2d_mode_t mode;
//     filter_padding_t pad;
// } filter2d_t;

typedef struct {
    int len;
    int kernel; // assume odd number;
    element_t *buf;
    element_t *out;
    filter_padding_t pad;
} filter1d_t;

filter1d_t *create_filter1d(int len, int kernel, filter_padding_t pad);
void destroy_filter1d(filter1d_t *filter);

void meanfilter_one_dim(array2d_t *out, const array2d_t* in, filter1d_t *filter, array2d_op_mode_t dim);
void medfilter_one_dim(array2d_t *out, const array2d_t* in, filter1d_t *filter, array2d_op_mode_t dim);
// void medfilter2d(array2d_t *out, const array2d_t *in, filter2d_t filter);
// void meanfilter2d(array2d_t *out, const array2d_t *in, filter2d_t filter);

#endif