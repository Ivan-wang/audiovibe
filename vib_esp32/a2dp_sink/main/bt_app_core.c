/*
   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/

#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include "freertos/xtensa_api.h"
#include "freertos/FreeRTOSConfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "bt_app_core.h"
#include "driver/i2s.h"
#include "freertos/ringbuf.h"

#include "fft.h"
#include "MD_MAX72xx.h"

/*******************************
 * STATIC FUNCTION DECLARATIONS
 ******************************/

/* handler for application task */
static void bt_app_task_handler(void *arg);
/* handler for I2S task */
static void bt_i2s_task_handler(void *arg);
/* message sender */
static bool bt_app_send_msg(bt_app_msg_t *msg);
/* handle dispatched messages */
static void bt_app_work_dispatched(bt_app_msg_t *msg);

static void data_i2s_task_handler(void *arg);

/*******************************
 * STATIC VARIABLE DEFINITIONS
 ******************************/

static xQueueHandle s_bt_app_task_queue = NULL;  /* handle of work queue */
static xTaskHandle s_bt_app_task_handle = NULL;  /* handle of application task  */
static xTaskHandle s_bt_i2s_task_handle = NULL;  /* handle of I2S task */
static RingbufHandle_t s_ringbuf_i2s = NULL;     /* handle of ringbuffer for I2S */

static xQueueHandle s_bt_map_task_queue = NULL;
static xTaskHandle s_data_i2s_task_handle = NULL;

// static spi_device_handle_t s_data_spi_handle = NULL;
// static xTaskHandle s_data_spi_task_handle = NULL;

#define FFT_LEN 256
#define COMPLEX_FFT_LEN 512
#define ENERGE_THRESHOLD 8000 
float l_data[COMPLEX_FFT_LEN], r_data[COMPLEX_FFT_LEN];
/*******************************
 * STATIC FUNCTION DEFINITIONbS
 ******************************/

static bool bt_app_send_msg(bt_app_msg_t *msg)
{
    if (msg == NULL) {
        return false;
    }

    if (xQueueSend(s_bt_app_task_queue, msg, 10 / portTICK_RATE_MS) != pdTRUE) {
        ESP_LOGE(BT_APP_CORE_TAG, "%s xQueue send failed", __func__);
        return false;
    }
    return true;
}

static void bt_app_work_dispatched(bt_app_msg_t *msg)
{
    if (msg->cb) {
        msg->cb(msg->event, msg->param);
    }
}

static void bt_app_task_handler(void *arg)
{
    bt_app_msg_t msg;

    for (;;) {
        /* receive message from work queue and handle it */
        if (pdTRUE == xQueueReceive(s_bt_app_task_queue, &msg, (portTickType)portMAX_DELAY)) {
            ESP_LOGD(BT_APP_CORE_TAG, "%s, signal: 0x%x, event: 0x%x", __func__, msg.sig, msg.event);

            switch (msg.sig) {
            case BT_APP_SIG_WORK_DISPATCH:
                bt_app_work_dispatched(&msg);
                break;
            default:
                ESP_LOGW(BT_APP_CORE_TAG, "%s, unhandled signal: %d", __func__, msg.sig);
                break;
            } /* switch (msg.sig) */

            if (msg.param) {
                free(msg.param);
            }
        }
    }
}

static void bt_i2s_task_handler(void *arg)
{
    uint8_t *data = NULL;
    size_t item_size = 0;
    size_t bytes_written = 0;
    i2s_port_t i2s_num = 1;

    for (;;) {
        /* receive data from ringbuffer and write it to I2S DMA transmit buffer */
        data = (uint8_t *)xRingbufferReceiveUpTo(s_ringbuf_i2s, &item_size, (portTickType)portMAX_DELAY, FFT_LEN*2*sizeof(uint16_t));
        if (item_size != 0){
            i2s_write(i2s_num, data, item_size, &bytes_written, portMAX_DELAY);
        }

        if (item_size != FFT_LEN*2*sizeof(uint16_t)) {
            ESP_LOGI(BT_APP_CORE_TAG, "dl -->> %d", item_size);
        }
        else {
            if (uxQueueMessagesWaiting(s_bt_map_task_queue) == 0) {
                // when fft handler is idle
                int l_sample = 0, r_sample = 0;
                for (int i = 0; i < FFT_LEN * 2 * sizeof(uint16_t); i+=4) {
                    l_sample = (int16_t)(((*(data + i + 1) << 8) | *(data + i)));
                    r_sample = (int16_t)(((*(data + i + 3) << 8) | *(data + i + 2)));

                    l_data[i>>1] = (float)l_sample;
                    r_data[i>>1] = (float)r_sample;
                }
                // send an int to queue to notify data mapping task, any int works here
                xQueueSend(s_bt_map_task_queue, &item_size, portMAX_DELAY);
            }
            else {
                ESP_LOGI(BT_APP_CORE_TAG, "missed frame");
            }
        }
        vRingbufferReturnItem(s_ringbuf_i2s, (void *)data);
    }
}

static void data_i2s_task_handler(void *arg)
{
    int msg;
    fft_config_t *lfft = fft_init(FFT_LEN, FFT_COMPLEX, FFT_FORWARD, l_data, NULL);
    fft_config_t *rfft = fft_init(FFT_LEN, FFT_COMPLEX, FFT_FORWARD, r_data, NULL);
    
    // audio sample rate 44100, i2s data rate 6000
    // use 1/8 of FFT LEN
    size_t data_len = FFT_LEN / 8;
    uint8_t data[data_len];
    
    for (int i = 0; i < data_len; ++i) {
        if (i & 0x00000001) {
            data[i] = 255;
        }
        else { data[i] = 0; }
    }

    size_t item_written;
    for (;;) {
        if (xQueuePeek(s_bt_map_task_queue, &msg, portMAX_DELAY)) {
            // use data to calculate FFT, the release resource
            float sum = 0.;
            for (int i = 0; i < FFT_LEN; ++i) {
                // sum += (l_data[i<<1] + r_data[i<<1]) / 2;
                sum += (sqrt(l_data[i<<1]*l_data[i<<1]) + sqrt(r_data[i<<1]*r_data[i<<1])) / 2;
            }
            sum /= FFT_LEN;
            sum /= ENERGE_THRESHOLD;
            if (sum > 1.) { sum = 1; }

            uint8_t frame_eng = (uint8_t)(sum * 255.);
            memset(data, frame_eng, data_len);

            fft_execute(lfft);
            fft_execute(rfft);

            xQueueReceive(s_bt_map_task_queue, &msg, 0);
            i2s_write(0, data, data_len, &item_written, portMAX_DELAY);
        }
        // write some data
    }

}


/********************************
 * EXTERNAL FUNCTION DEFINITIONS
 *******************************/

bool bt_app_work_dispatch(bt_app_cb_t p_cback, uint16_t event, void *p_params, int param_len, bt_app_copy_cb_t p_copy_cback)
{
    ESP_LOGD(BT_APP_CORE_TAG, "%s event: 0x%x, param len: %d", __func__, event, param_len);

    bt_app_msg_t msg;
    memset(&msg, 0, sizeof(bt_app_msg_t));

    msg.sig = BT_APP_SIG_WORK_DISPATCH;
    msg.event = event;
    msg.cb = p_cback;

    if (param_len == 0) {
        return bt_app_send_msg(&msg);
    } else if (p_params && param_len > 0) {
        if ((msg.param = malloc(param_len)) != NULL) {
            memcpy(msg.param, p_params, param_len);
            /* check if caller has provided a copy callback to do the deep copy */
            if (p_copy_cback) {
                p_copy_cback(msg.param, p_params, param_len);
            }
            return bt_app_send_msg(&msg);
        }
    }

    return false;
}

void bt_app_task_start_up(void)
{
    s_bt_app_task_queue = xQueueCreate(10, sizeof(bt_app_msg_t));
    xTaskCreate(bt_app_task_handler, "BtAppTask", 3072, NULL, 10, &s_bt_app_task_handle);
}

void bt_app_task_shut_down(void)
{
    if (s_bt_app_task_handle) {
        vTaskDelete(s_bt_app_task_handle);
        s_bt_app_task_handle = NULL;
    }
    if (s_bt_app_task_queue) {
        vQueueDelete(s_bt_app_task_queue);
        s_bt_app_task_queue = NULL;
    }
}

void bt_i2s_task_start_up(void)
{
    if ((s_ringbuf_i2s = xRingbufferCreate(8 * 1024, RINGBUF_TYPE_BYTEBUF)) == NULL) {
        return;
    }
    
    if ((s_bt_map_task_queue = xQueueCreate(1, sizeof(int))) == NULL) {
        return;
    }
    xTaskCreatePinnedToCore(bt_i2s_task_handler, "BtI2STask", 9012, NULL, configMAX_PRIORITIES - 3, &s_bt_i2s_task_handle, 0);
    xTaskCreatePinnedToCore(data_i2s_task_handler, "DataI2STask", 9012, NULL, configMAX_PRIORITIES - 4, &s_data_i2s_task_handle, 1);

}

void bt_i2s_task_shut_down(void)
{
    if (s_bt_i2s_task_handle) {
        vTaskDelete(s_bt_i2s_task_handle);
        s_bt_i2s_task_handle = NULL;
    }
    if (s_ringbuf_i2s) {
        vRingbufferDelete(s_ringbuf_i2s);
        s_ringbuf_i2s = NULL;
    }
    if (s_bt_map_task_queue) {
        vQueueDelete(s_bt_map_task_queue);
        s_bt_map_task_queue = NULL;
    }
    if (s_data_i2s_task_handle) {
        vTaskDelete(s_data_i2s_task_handle);
        s_data_i2s_task_handle = NULL;
    }
}

size_t write_ringbuf(const uint8_t *data, size_t size)
{
    BaseType_t done = xRingbufferSend(s_ringbuf_i2s, (void *)data, size, (portTickType)portMAX_DELAY);

    return done ? size : 0;
}
