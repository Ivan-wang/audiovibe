#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdbool.h>
#include <string.h> // for memset
#include "array2d.h"
#include "filter.h"
#include "peak.h"
#include "config.h"
#include "stft.h" // for FFT_FREQ_128_22050
#include "hrps.h"

const int NUM_PEAKS_LIMIT = 5;
extern const element_t FFT_FREQ_128_22050[65];

// utils
int find_frq_bin_128(element_t freq) {
    int ind = 0;
    while (ind < 64 && FFT_FREQ_128_22050[ind] < freq) { ind++; }

    if (FFT_FREQ_128_22050[ind]-freq < freq - FFT_FREQ_128_22050[ind-1]) {
        return ind;
    }
    else {
        return ind-1;
    }
}
void find_bandwidth(int *lo, int *hi, element_t *spec, int bin, int total_bin, element_t cut_off) {
    element_t val =  spec[bin];

    for (*lo = bin; *lo >= 0; *lo = *lo-1) {
        if (spec[*lo] < cut_off * val) {
            break;
        }
    }

    for (*hi = bin+1; bin < total_bin; *hi = *hi+1) {
        if (spec[*hi] < cut_off * val) {
            break;
        }
    }

}
void remove_harmonics(element_t *peak_mask, element_t *masked_spec, element_t *freqs, int len) {
    
}

peak_handler_t *create_peak_handler(int h_spec, int w_spec, int filter_len, int relative_th, int global_th, hrps_args_t *hrps_args){
    peak_handler_t *peaks = (peak_handler_t*)malloc(sizeof(peak_handler_t));

    peaks->relative_th = relative_th;
    peaks->global_th = global_th;

    peaks->spec_db = create_array2d(h_spec, w_spec, NULL);
    peaks->buf = create_array2d(h_spec, w_spec, NULL);
    peaks->reduce_buf = (element_t*)malloc(h_spec*sizeof(element_t));
    peaks->peaks = create_array2d(h_spec, w_spec, NULL);
    peaks->filter = create_filter1d(w_spec, filter_len, FILTER_PAD_NEAREST); // filter on freq dim (DIM1)

    peaks->hrps_handler = create_hrps_from_args(hrps_args);
    peaks->argsort_handler = create_argsort_handler(w_spec, NULL);
    return peaks;
}

peak_handler_t *create_peak_handler_from_args(peak_args_t *peak_args, hrps_args_t *hrps_args) {
    return create_peak_handler(peak_args->h_spec, peak_args->w_spec, peak_args->filter_len,
        peak_args->relative_th, peak_args->globa_th, hrps_args);
}

void destroy_peak_handler(peak_handler_t *peaks) {
    destroy_array2d(peaks->peaks);
    destroy_array2d(peaks->spec_db);
    destroy_array2d(peaks->buf);
    destroy_filter1d(peaks->filter);

    free(peaks->reduce_buf);

    destroy_hrps(peaks->hrps_handler);
    destroy_argsort_handler(peaks->argsort_handler);
    free(peaks);
}

void extract_peaks(peak_handler_t *peaks, const array2d_t *spec) {
    int dim0 = spec->dim0;
    int dim1 = spec->dim1;

    // HRPS
    exec_hrps(peaks->hrps_handler, spec);

    // PREPARE FOR PEAK EXTRACTION
    array2d_fill(peaks->peaks, 1.); // peak masks
    array2d_copy(peaks->peaks, spec); // copy spec to peaks handler
    array2d_db(peaks->spec_db, spec, 1., 1e-10, 80.); // extracting is based on db scale

    // STEGE 1
    // Eliminating 1: same value??
    for (int i = 0; i < dim0; ++i) { // time
        int is_the_same = 1;
        for (int j = 0; j < dim1; ++j) {
            if (fabsf(peaks->spec_db->data[i][j] - peaks->spec_db->data[i][0]) > 1e-5) {
                is_the_same = 0;
                break;
            }
        }
        if (is_the_same) {
            memset(peaks->peaks->data[i], 0, spec->dim1*sizeof(element_t));
        }
    }

    // apply relative threshold
    meanfilter_one_dim(peaks->buf, peaks->spec_db, peaks->filter, ARRAY_2D_DIM1); // mean filter on freq dim (DIM1)
    for (int i = 0; i < spec->dim0; ++i) {
        for (int j = 0; j < spec->dim1; ++j) {
            if (peaks->spec_db->data[i][j] - peaks->buf->data[i][j] < peaks->relative_th) {
                peaks->peaks->data[i][j] = 0.;
            }
        }
    }

    // apply global threshold
    array2d_max(peaks->reduce_buf, peaks->spec_db, ARRAY_2D_DIM1);
    for (int i = 0; i < spec->dim0; ++i) {
        peaks->reduce_buf[i] -= peaks->global_th;
        for (int j = 0; j < spec->dim1; ++j) {
            if (peaks->spec_db->data[i][j] - peaks->reduce_buf[i] < 0.) {
                peaks->peaks->data[i][j] = 0.;
            }
        }
    }

    // apply local maxima
    // TODO number local maxima is are_all_equal to (dim0 x 1/2 dim1 x 2)
    // int num_args = 

    // STAGE 2: reduce the peaks numbers
    for (int ti = 0; ti < peaks->peaks->dim0; ++ti) {
        refine_peaks(peaks, spec, ti);
    }
}

int determine_harmonic_peaks(element_t *spec, element_t *orispec, argsort_handler_t *handle, int len) {
    int num_peaks = 0;
    refill_argsort_handler(handle, spec);
    argsort(handle);

    for (int i = 0; i < len/2+1; ++i) {
        if (spec[handle->base[i].index] == 0. ) { 
            continue;
        }

        // find a new peak; clear its band and overtone's band
        // cutoff factor to determine BW is 0.5
        num_peaks += 1;

        // determine base band width
        // NOTE: we need to use original spec (not masked) to determine bandwidth
        int mid = handle->base[i].index;
        int lo = mid;
        int hi = mid;
        while (lo > 0 && orispec[lo] > 0.5 * orispec[mid]) {--lo;}
        while (hi < len-1 && orispec[hi] > 0.5 * orispec[mid]) { ++hi; }
        
        float base_freq = FFT_FREQ_128_22050[mid];
        float bandwidth = FFT_FREQ_128_22050[hi] - FFT_FREQ_128_22050[lo];
        
        // remove harmonics
        for (int f = 2; base_freq*(float)f < FFT_FREQ_128_22050[64]; ++f) {
            float center_freq = base_freq * (float)f;
            float center_bw = bandwidth * (float)f;
            int lo_bin = find_frq_bin_128(center_freq - center_bw / 2);
            int hi_bin = find_frq_bin_128(center_freq + center_bw / 2);
            for (int bin = lo_bin; bin <= hi_bin && bin<len; ++bin) {
                if (bin == mid) {
                    continue; // do not modify the main peak freq
                }
                spec[bin] = 0.;
            }
        }
    }

    return num_peaks;
}

void refine_peaks(peak_handler_t *peaks, const array2d_t *linspec, int index) {
    element_t sum = 0.,  ratioH = 0., ratioP = 0., ratioR = 0;
    bool are_all_equal = true;

    element_t *curr_linspec = linspec->data[index];
    element_t *spec = peaks->peaks->data[index];
    element_t *harmonic = peaks->hrps_handler->hormonic->data[index];
    element_t *percussive = peaks->hrps_handler->percussive->data[index];
    element_t *residual = peaks->hrps_handler->residual->data[index];
    argsort_handler_t *sort_handler = peaks->argsort_handler;
    int len = peaks->peaks->dim1;

    // sum power
    for (int i = 0; i < len; ++i) {
        ratioH += harmonic[i];
        ratioP += percussive[i];
        ratioR += residual[i];
        sum += curr_linspec[i];
        // check whether all element is same
        are_all_equal = are_all_equal && curr_linspec[i]==curr_linspec[0];
    }

    if (sum < 1e-5 || are_all_equal) {
        // printf("[0] \t Index {%d} \t Num Peak 0\n", index);
        memset(spec, 0, len * sizeof(element_t)); // no peaks
        return;
    }

    ratioH /= sum;
    ratioR /= sum;
    ratioP /= sum;

    int num_peaks = 0;
    // determine # of peaks
    if (ratioP > 2.*ratioR && ratioP > 2.*ratioH) {
        // printf("[P] \t Index {%d} \t Num Peak 3\n", index);
        num_peaks = 3;
    }
    else if (ratioR > 2.*ratioH && ratioR > 2.*ratioP) {
        // printf("[R] \t Index {%d} \t Num Peak 2\n", index);
        num_peaks = 2;
    }
    else if (ratioH > 2.*ratioP && ratioH > 2.*ratioR) {
        num_peaks = determine_harmonic_peaks(spec, curr_linspec, peaks->argsort_handler, len);
        if (num_peaks > NUM_PEAKS_LIMIT) {
            num_peaks = NUM_PEAKS_LIMIT;
        }
        // printf("[H] \t Index {%d} \t Num Peak %d\n", index, num_peaks);
    }
    else {
        num_peaks = NUM_PEAKS_LIMIT;
        // printf("[D] \t Index {%d} \t Num Peak %d\n", index, num_peaks);
    }

    // re-sort spec: cause harmonic elimination may modify the spec inplace
    refill_argsort_handler(sort_handler, spec);
    argsort(sort_handler);

    // clearn up peaks
    for (int i = num_peaks; i < len; ++i) {
        spec[sort_handler->base[i].index] = 0.;
    }
}