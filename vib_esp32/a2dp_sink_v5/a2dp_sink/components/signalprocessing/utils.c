#include <stdlib.h>
#include "utils.h"

int less(const void *a, const void *b)
{
    argsort_elem_t *a1 = (argsort_elem_t*)a;
    argsort_elem_t *a2 = (argsort_elem_t *)b;
    if ((*a1).element < (*a2).element)
        return 1;
    else
        return -1;
}

argsort_handler_t* create_argsort_handler(int len, float *data) {
    argsort_handler_t *handler = (argsort_handler_t*)malloc(sizeof(argsort_handler_t));
    handler->len = len;
    handler->base = (argsort_elem_t*)malloc(sizeof(argsort_elem_t)*len);

    refill_argsort_handler(handler, data);

    return handler;
}

void refill_argsort_handler(argsort_handler_t *handler, float *data) {
    if (data == NULL) {
        return;
    }
    for (int i = 0; i < handler->len; ++i) {
        handler->base[i].element = data[i];
        handler->base[i].index = i;
    }
}

void argsort(argsort_handler_t *handler) {
    qsort(handler->base, handler->len, sizeof(argsort_elem_t), less);
}

void destroy_argsort_handler(argsort_handler_t *handler) {
    free(handler->base);
    free(handler);
}

int read_bin_file(const char* file, float* data, int len) {
    FILE *fp = fopen(file, "rb");

    if (!fp) {
        printf("Cannot Open File %s\n", file);
        return -1;
    }
    int read_len = fread(data, sizeof(float), len, fp);
    fclose(fp);
    
    return read_len;
}