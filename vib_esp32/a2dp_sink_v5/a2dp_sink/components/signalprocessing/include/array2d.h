#ifndef _ARRAY_2D_H_
#define _ARRAY_2D_H_

typedef float element_t;

typedef enum {
    ARRAY_2D_ELEMENTWISE = 0,
    ARRAY_2D_DIM0,
    ARRAY_2D_DIM1,
    ARRAY_2D_DIM0_DIM1,
    ARRAY_OP_MAX
} array2d_op_mode_t;

typedef struct {
    element_t **data;

    int dim0;
    int dim1;
} array2d_t;

array2d_t *create_array2d(int dim0, int dim1, element_t *raw);
void destroy_array2d(array2d_t *arr);

void array2d_dump(element_t *raw, array2d_t *arr);
void array2d_fill(array2d_t *arr, element_t val);
void array2d_fill_data(array2d_t *arr, element_t *raw);
void array2d_cmp(int *out, const array2d_t *arr1, const array2d_t *arr2);
void array2d_copy(array2d_t *dst, const array2d_t *src);
void array2d_shift(array2d_t *dst, int offset, array2d_op_mode_t mode);
void array2d_shift_append_raw(array2d_t *dst, int offset, array2d_op_mode_t mode, const element_t *in);

// reduce
void array2d_sum(element_t *out, const array2d_t *arr, array2d_op_mode_t mode);
void array2d_mean(element_t *out, const array2d_t *arr, array2d_op_mode_t mode);
void array2d_var(element_t *out, const array2d_t *arr, array2d_op_mode_t mode);
void array2d_max(element_t *out, const array2d_t *arr, array2d_op_mode_t mode);

// elementwise transforms
void array2d_db(array2d_t *out, const array2d_t *arr, element_t ref, element_t amin, element_t top_db);
void array2d_square(array2d_t *out, const array2d_t *arr);

// signals
void argrelextreme_maximal(int **arg, int *num, const array2d_t *arr, array2d_op_mode_t mode, int num_args);

// debugging
void array2d_display(const array2d_t *arr);

#endif