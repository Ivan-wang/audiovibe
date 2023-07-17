#include <stdio.h> // printf
#include <string.h> // memset
#include <stdlib.h> // max ?  NO
#include <math.h>
#include "array2d.h"

int imax(int a, int b) {
    return a > b ? a : b;
}
int imin(int a, int b) {
    return a < b ? a : b;
}

// TODO: Unsupported op mode should send out warning
array2d_t *create_array2d(int dim0, int dim1, element_t *raw) {
    array2d_t *arr = (array2d_t *)malloc(sizeof(array2d_t));

    arr->data = (element_t**)malloc(dim0*sizeof(element_t*));

    if (raw == NULL) {
        for (int i = 0; i < dim0; ++i) {
            arr->data[i] = (element_t*)malloc(dim1*sizeof(element_t));
            memset(arr->data[i], 0, dim1*sizeof(element_t));
        }
    }
    else {
        element_t *pdata = raw;
        for (int i = 0; i < dim0; ++i) {
            arr->data[i] = (element_t*)malloc(dim1*sizeof(element_t));
            memcpy(arr->data[i], pdata, dim1*sizeof(element_t));
            pdata += dim1;
        }
    }
    arr->dim0 = dim0;
    arr->dim1 = dim1;
    return arr;
}

void destroy_array2d(array2d_t *arr) {
    if (arr->data == NULL) { return; }

    for (int i = 0; i < arr->dim0; ++i) {
        if (arr->data[i] != NULL) {
            free(arr->data[i]);
            arr->data[i] = NULL;
        }
    }
    free(arr->data);
    arr->data = NULL;
}

void array2d_dump(element_t *raw, array2d_t *arr) {
    int pos = 0;
    for (int i = 0; i < arr->dim0; ++i) {
        for (int j = 0; j < arr->dim1; ++j) {
            raw[pos++] = arr->data[i][j];
        }
    }
}

void array2d_fill(array2d_t *arr, element_t val) {
    for (int i = 0; i < arr->dim0; ++i) {
        for (int j = 0; j < arr->dim1; ++j) {
            arr->data[i][j] = val;
        }
    }
}

void array2d_fill_data(array2d_t *arr, element_t *raw) {
    for (int i = 0; i < arr->dim0; ++i) {
        for (int j = 0; j < arr->dim1; ++j) {
            arr->data[i][j] = raw[i*arr->dim1+j];
        }
    }
}

void array2d_cmp(int *out, const array2d_t *arr1, const array2d_t *arr2) {
    *out = 0;
    for (int i = 0; i < arr1->dim0; ++i) {
        for (int j = 0; j < arr2->dim1; ++j) {
            if (fabsf(arr1->data[i][j]-arr2->data[i][j]) > 1e-4) {
                *out += 1;
            }
        }
    }
}

void array2d_copy(array2d_t *dst, const array2d_t *src) {
    for (int i = 0; i < src->dim0; ++i) {
        for (int j = 0; j < src->dim1; ++j) {
            dst->data[i][j] = src->data[i][j];
        }
    }
    
}

// assert offset is positive
void array2d_shift(array2d_t *dst, int offset, array2d_op_mode_t mode) {
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0_DIM1:
        break;
    case ARRAY_2D_DIM0:
    {
        // changing pointers, not copying data
        int shift_len = dst->dim0 - offset;
        element_t* tmp[offset];
        memcpy(tmp, dst->data, offset * sizeof(element_t*));
        memcpy(dst->data, dst->data+offset, shift_len * sizeof(element_t*));
        memcpy(dst->data+shift_len, tmp, offset * sizeof(element_t*));
        break;
    } 
    case ARRAY_2D_DIM1:
    {
        int shift_len = dst->dim1 - offset;
        for (int i = 0; i < dst->dim0; ++i) {
            memcpy(dst->data[i], dst->data[i]+offset, shift_len * sizeof(element_t));
            // memset(dst->data[i]+offset, 0, offset * sizeof(element_t)); // no cleaning...
        }
        break;
    }
    default:
        break;
    }
}

void array2d_shift_append_raw(array2d_t *dst, int offset, array2d_op_mode_t mode, const element_t *raw) {
    array2d_shift(dst, offset, mode);
    if (raw == NULL) { return; }
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0_DIM1:
        break;
    case ARRAY_2D_DIM0:
    {
        int shift_len = dst->dim0 - offset;
        const element_t *data = raw;
        for (int i = 0; i < offset; ++i) {
            memcpy(dst->data[i+shift_len], data, dst->dim1 * sizeof(element_t));
            data += dst->dim1;
        }
        break;
    }
    case ARRAY_2D_DIM1:
    {
        int shift_len = dst->dim1 - offset;
        const element_t *data = raw;
        for (int i = 0; i < dst->dim0; ++i) {
            memcpy(dst->data[i]+shift_len, data, offset * sizeof(element_t));
            data += offset;
        }
        break;
    }
    default:
        break;
    }
}

void array2d_sum(element_t *out, const array2d_t *arr, array2d_op_mode_t mode) {
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0:
    {
        memset(out, 0, sizeof(element_t)*arr->dim1);
        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                out[j] += arr->data[i][j];
            }
        }
        break;
    }
    case ARRAY_2D_DIM1:
    {
        memset(out, 0, sizeof(element_t)*arr->dim0);
        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                out[i] += arr->data[i][j];
            }
        }
        break;
    }
    case ARRAY_2D_DIM0_DIM1:
    {
        *out = 0.;
        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                *out += arr->data[i][j];
            }
        }
        break;
    }
    default:
        break;
    }
}

void array2d_mean(element_t *out, const array2d_t *arr, array2d_op_mode_t mode) {
    array2d_sum(out, arr, mode);
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0:
    {
        for (int i = 0; i < arr->dim1; ++i) {
            out[i] /= arr->dim0;
        }
        break;
    }
    case ARRAY_2D_DIM1:
    {
        for (int i = 0; i < arr->dim0; ++i) {
            out[i] /= arr->dim1;
        }
        break;
    }
    case ARRAY_2D_DIM0_DIM1:
    {
        *out /= (arr->dim0 * arr->dim1);
        break;
    }
    default:
        break;
    }
}

void array2d_var(element_t *out, const array2d_t *arr, array2d_op_mode_t mode) {
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0:
    {
        array2d_mean(out, arr, mode);
        for (int i = 0; i < arr->dim1; ++i) {
            element_t mean = out[i];
            out[i] = 0.;
            for (int j = 0; j < arr->dim0; ++j) {
                out[i] += (arr->data[j][i] - mean) * (arr->data[j][i] - mean);
            }
        }
        for (int i = 0; i < arr->dim1; ++i) {
            out[i] /= arr->dim0;
        }
        break;
    }
    case ARRAY_2D_DIM1:
    {
        array2d_mean(out, arr, mode);
        for (int i = 0; i < arr->dim0; ++i) {
            element_t mean = out[i];
            out[i] = 0.;
            for (int j = 0; j < arr->dim1; ++j) {
                out[i] += (arr->data[i][j] - mean) * (arr->data[i][j] - mean);
            }
        }
        for (int i = 0; i < arr->dim0; ++i) {
            out[i] /= arr->dim1;
        }
        break;
    }
    case ARRAY_2D_DIM0_DIM1:
    {
        array2d_mean(out, arr, mode);
        element_t mean = *out;
        *out = 0.;

        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                out[i] += (arr->data[i][j] - mean) * (arr->data[i][j] - mean);
            }
        }
        *out /= arr->dim0 * arr->dim1;
        break;
    }
    default:
        break;
    }
}
void array2d_max(element_t *out, const array2d_t *arr, array2d_op_mode_t mode) {
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0:
    {
        for (int i = 0; i < arr->dim1; ++i) {
            out[i] = arr->data[0][i];
        }
        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                out[j] = fmaxf(arr->data[i][j], out[j]);
            }
        }
        break;
    }
    case ARRAY_2D_DIM1:
    {
        for (int i = 0; i < arr->dim0; ++i) {
            out[i] = arr->data[i][0];
        }
        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                out[i] = fmaxf(arr->data[i][j], out[i]);
            }
        }
        break;
    }
    case ARRAY_2D_DIM0_DIM1:
    {
        *out = arr->data[0][0];
        for (int i = 0; i < arr->dim0; ++i) {
            for (int j = 0; j < arr->dim1; ++j) {
                *out = fmaxf(arr->data[i][j], *out);
            }
        }
        break;
    }
    default:
        break;
    }
}

element_t _power_to_db(element_t power, element_t ref, element_t amin, element_t top_db) {
    float mag = fabsf(power);
    float db = 10. * log10f(fmaxf(mag, amin));
    db -= 10. * log10f(fmaxf(ref, amin));
    return db;
}

void array2d_db(array2d_t *out, const array2d_t *arr, element_t ref, element_t amin, element_t top_db) {
    for (int i = 0; i < arr->dim0; ++i) {
        for (int j = 0; j < arr->dim1; ++j) {
            out->data[i][j] = _power_to_db(arr->data[i][j], ref, amin, top_db);
        }
    }
}

void array2d_square(array2d_t *out, const array2d_t *arr) {
    for (int i = 0; i < arr->dim0; ++i) {
        for (int j = 0; j < arr->dim1; ++j) {
            out->data[i][j] = (arr->data[i][j]) * (arr->data[i][j]);
        }
    }
}

void argrelextreme_maximal(int **arg, int *num, const array2d_t *arr, array2d_op_mode_t mode, int num_args) {
    *num = 0;
    switch (mode)
    {
    case ARRAY_2D_ELEMENTWISE:
        break;
    case ARRAY_2D_DIM0:
    {
        for (int row = 1; row < arr->dim0-1; ++row) {
            for (int col = 0; col < arr->dim1; ++col) {
                if ((arr->data[row][col] >= arr->data[row-1][col] &&
                    arr->data[row][col] > arr->data[row+1][col]) ||
                    (arr->data[row][col] > arr->data[row-1][col] &&
                    arr->data[row][col] >= arr->data[row+1][col])) {
                        arg[0][*num] = row;
                        arg[1][*num] = col;
                        *num += 1;
                    }
                if (*num == num_args) { break; }
            }
            if (*num == num_args) { break; }
        }
        break;
    }
    case ARRAY_2D_DIM1:
    {
        for (int row = 0; row < arr->dim0; ++row) {
            for (int col = 1; col < arr->dim1-1; ++col) {
                if ((arr->data[row][col] >= arr->data[row][col-1] &&
                    arr->data[row][col] > arr->data[row][col+1]) ||
                    (arr->data[row][col] > arr->data[row][col-1] &&
                    arr->data[row][col] >= arr->data[row][col+1])) {
                        arg[0][*num] = row;
                        arg[1][*num] = col;
                        *num += 1;
                    }
                if (*num == num_args) { break; }
            }
            if (*num == num_args) { break; }
        }
        break;
    }
    case ARRAY_2D_DIM0_DIM1:
    {
        break;
    }
    default:
        break;
    }
}

void array2d_display(const array2d_t *arr) {
    for (int i = 0; i < arr->dim0; ++i) {
        for (int j = 0; j < arr->dim1; ++j) {
            printf("%f\t", arr->data[i][j]);
        }
        printf("\n");
    }
    printf("\n");
}