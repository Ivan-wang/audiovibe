#include <memory.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "filter.h"

// utils
filter1d_t *create_filter1d(int len, int kernel, filter_padding_t pad) {
    filter1d_t *filter = (filter1d_t*)malloc(sizeof(filter1d_t));
    filter->len = len;
    filter->kernel = kernel;
    filter->buf = (element_t*)malloc(sizeof(element_t)*(len+kernel-1));
    memset(filter->buf, 0, sizeof(element_t)*(len+kernel-1));
    filter->out = (element_t*)malloc(sizeof(element_t)*len);
    memset(filter->out, 0, sizeof(element_t)*len);
    filter->pad = pad;
    return filter;
}

void destroy_filter1d(filter1d_t *filter) {
    free(filter->buf);
    free(filter->out);
    free(filter);
}

void _pad_buffer1d(element_t *buffer, int len, int kernel, filter_padding_t pad) {
    int left = kernel / 2;
    for (int i = 0; i < left; ++i) {
        if (pad == FILTER_PAD_ZERO) { buffer[i] = 0.; }
        else {  buffer[i] = buffer[left]; }// nearest 
    }
    for (int i = left+len; i < len+kernel-1; ++i) {
        if (pad == FILTER_PAD_ZERO) { buffer[i] = 0.; }
        else { buffer[i] = buffer[left+len-1]; } // nearest
    }
}

void _meanfilter1d(filter1d_t *filter) {
    element_t running = 0.;
    for (int j = 0; j < filter->kernel; ++j) {
        running += filter->buf[j];
    }
    for (int j = 0; j < filter->len; ++j) {
        filter->out[j] = running / filter->kernel;
        running -= filter->buf[j];
        running += filter->buf[j+filter->kernel];
    }
}

void meanfilter_one_dim(array2d_t *out, const array2d_t* in, filter1d_t *filter, array2d_op_mode_t dim) {
    if (dim == ARRAY_2D_DIM0) {
        for (int i = 0; i < in->dim1; ++i) {
            int left = filter->kernel / 2;
            for (int j = 0; j < in->dim0; ++j) {
                filter->buf[left+j] = in->data[j][i];
            }

            _pad_buffer1d(filter->buf, filter->len, filter->kernel, filter->kernel);
            _meanfilter1d(filter);

            for (int j = 0; j < filter->len; ++j) {
                out->data[j][i] = filter->out[j];
            }
        }
    }
    else {
        for (int i = 0; i < in->dim0; ++i) {
            int left = filter->kernel / 2;
            memcpy(filter->buf+left, in->data[i], sizeof(element_t)*filter->len);
            _pad_buffer1d(filter->buf, filter->len, filter->kernel, filter->kernel);
            _meanfilter1d(filter);
            memcpy(out->data[i], filter->out, filter->len*sizeof(element_t));
        }
    }
}

void _medfilter1d(filter1d_t *filter) {
    element_t *win = (element_t*)malloc(sizeof(element_t)*filter->kernel);

    for (int i = 0; i < filter->len; ++i) {
        // window
        memcpy(win, filter->buf+i, sizeof(element_t)*filter->kernel);
        // sort window
        for (int j = 0; j < filter->kernel/2+1; ++j) {
            int min = j;
            for (int k = j; k < filter->kernel; ++k) {
                if (win[k] < win[min]) { min = k; }
            }
            element_t tmp = win[j];
            win[j] = win[min];
            win[min] = tmp;
        }
        // result
        filter->out[i] = win[filter->kernel>>1];
    }

    free(win);
}
void medfilter_one_dim(array2d_t *out, const array2d_t* in, filter1d_t *filter, array2d_op_mode_t dim) {
    if (dim == ARRAY_2D_DIM0) {
        for (int i = 0; i < in->dim1; ++i) {
            // copy data
            int left = filter->kernel / 2;
            for (int j = 0; j < in->dim0; ++j) {
                filter->buf[left+j] = in->data[j][i];
            }

            _pad_buffer1d(filter->buf, filter->len, filter->kernel, filter->pad);
            _medfilter1d(filter);

            for (int j = 0; j < filter->len; ++j) {
                out->data[j][i] = filter->out[j];
            }
        }
    }
    else {
        for (int i = 0; i < in->dim0; ++i) {
            int left = filter->kernel / 2;
            memcpy(filter->buf+left, in->data[i], sizeof(element_t)*filter->len);

            _pad_buffer1d(filter->buf, filter->len, filter->kernel, filter->pad);
            _medfilter1d(filter);

            memcpy(out->data[i], filter->out, filter->len*sizeof(element_t));
        }
    }
}
