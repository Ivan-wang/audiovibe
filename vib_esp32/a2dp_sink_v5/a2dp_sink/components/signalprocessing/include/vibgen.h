#ifndef _VIBGEN_H_
#define _VIBGEN_H_
#include "array2d.h"


typedef struct  
{
    int frame_len; // len of one frame 
    int frame_num; // num of frames 

    float frame_time_sec;

    float freq_bias;
    float freq_scale;
    array2d_t *vibration; // the same dimesion of STFT spec
} vib_handler_t;

vib_handler_t *create_vib_handler(int frame_num, int frame_len, float frame_time_sec, float freq_bias, float freq_scale);
void generate_vibration(vib_handler_t *handler, const array2d_t *peaks);
void destroy_vib_handler(vib_handler_t *handler);

vib_handler_t *init_vib_handler();

#endif
