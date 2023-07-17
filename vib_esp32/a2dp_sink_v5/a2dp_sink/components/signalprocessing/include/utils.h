#include <stdio.h>
#include <stdlib.h>

// arg sort
typedef struct {
    float element;
    int index;
} argsort_elem_t;

typedef struct {
    argsort_elem_t *base;
    int len;
} argsort_handler_t;

argsort_handler_t* create_argsort_handler(int len, float* data);
void refill_argsort_handler(argsort_handler_t *handler, float *data);
void argsort(argsort_handler_t *handler);
void destroy_argsort_handler(argsort_handler_t *handler);


int read_bin_file(const char* file, float* data, int len);