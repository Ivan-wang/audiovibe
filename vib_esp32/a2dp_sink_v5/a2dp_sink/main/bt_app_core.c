/*
 * SPDX-FileCopyrightText: 2021-2022 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Unlicense OR CC0-1.0
 */

#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include "freertos/xtensa_api.h"
#include "freertos/FreeRTOSConfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "bt_app_core.h"
#include "bt_sig_proc.h"
// #ifdef CONFIG_EXAMPLE_A2DP_SINK_OUTPUT_INTERNAL_DAC
#include "driver/dac_continuous.h"
// #else
#include "driver/i2s_std.h"
// #endif
#include "freertos/ringbuf.h"


#define RINGBUF_HIGHEST_WATER_LEVEL    (32 * 1024)
#define RINGBUF_PREFETCH_WATER_LEVEL   (20 * 1024)

enum {
    RINGBUFFER_MODE_PROCESSING,    /* ringbuffer is buffering incoming audio data, I2S is working */
    RINGBUFFER_MODE_PREFETCHING,   /* ringbuffer is buffering incoming audio data, I2S is waiting */
    RINGBUFFER_MODE_DROPPING       /* ringbuffer is not buffering (dropping) incoming audio data, I2S is working */
};

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

/*******************************
 * STATIC VARIABLE DEFINITIONS
 ******************************/

static QueueHandle_t s_bt_app_task_queue = NULL;  /* handle of work queue */
static TaskHandle_t s_bt_app_task_handle = NULL;  /* handle of application task  */
static TaskHandle_t s_bt_i2s_task_handle = NULL;  /* handle of I2S task */
static RingbufHandle_t s_ringbuf_i2s = NULL;     /* handle of ringbuffer for I2S */
static SemaphoreHandle_t s_i2s_write_semaphore = NULL;
static uint16_t ringbuffer_mode = RINGBUFFER_MODE_PROCESSING;

static QueueHandle_t s_bt_sig_task_queue = NULL;
static TaskHandle_t s_sig_proc_task_handle = NULL;
static SemaphoreHandle_t s_sig_write_semaphore = NULL;
static SemaphoreHandle_t s_sig_read_semaphore = NULL;

#define FFT_LEN 128
#define DAC_LEN 64
#define COMPLEX_FFT_LEN 512

float l_data[FFT_LEN], r_data[FFT_LEN];
uint8_t dac_buf[DAC_LEN];
/*********************************
 * EXTERNAL FUNCTION DECLARATIONS
 ********************************/
#ifndef CONFIG_EXAMPLE_A2DP_SINK_OUTPUT_INTERNAL_DAC
extern i2s_chan_handle_t tx_chan;
extern dac_continuous_handle_t sig_chan;
extern audio_handler_t* sig_proc_handler;
#else
extern dac_continuous_handle_t tx_chan;
#endif

/*******************************
 * STATIC FUNCTION DEFINITIONS
 ******************************/

static bool bt_app_send_msg(bt_app_msg_t *msg)
{
    if (msg == NULL) {
        return false;
    }

    /* send the message to work queue */
    if (xQueueSend(s_bt_app_task_queue, msg, 10 / portTICK_PERIOD_MS) != pdTRUE) {
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
        if (pdTRUE == xQueueReceive(s_bt_app_task_queue, &msg, (TickType_t)portMAX_DELAY)) {
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
    /**
     * The total length of DMA buffer of I2S is:
     * `dma_frame_num * dma_desc_num * i2s_channel_num * i2s_data_bit_width / 8`.
     * Transmit `dma_frame_num * dma_desc_num` bytes to DMA is trade-off.
     */
    // const size_t item_size_upto = 240 * 6;
    const size_t item_size_upto = FFT_LEN * 2 * 2; // FFT LEN * 2 CHANNEL * UINT16
    size_t bytes_written = 0;

    for (;;) {
        if (pdTRUE == xSemaphoreTake(s_i2s_write_semaphore, portMAX_DELAY)) {
            for (;;) {
                item_size = 0;
                /* receive data from ringbuffer and write it to I2S DMA transmit buffer */
                data = (uint8_t *)xRingbufferReceiveUpTo(s_ringbuf_i2s, &item_size, (TickType_t)pdMS_TO_TICKS(20), item_size_upto);
                if (item_size == 0) {
                    ESP_LOGI(BT_APP_CORE_TAG, "ringbuffer underflowed! mode changed: RINGBUFFER_MODE_PREFETCHING");
                    ringbuffer_mode = RINGBUFFER_MODE_PREFETCHING;
                    break;
                }
            #ifdef CONFIG_EXAMPLE_A2DP_SINK_OUTPUT_INTERNAL_DAC
                dac_continuous_write(tx_chan, data, item_size, &bytes_written, -1);
            #else
                // i2s_channel_write(tx_chan, data, item_size, &bytes_written, portMAX_DELAY);
            #endif
                // convert 16bit data to float for signal processing

                // alway send audio
                // i2s_channel_write(tx_chan, data, item_size, &bytes_written, portMAX_DELAY);
                if (item_size != item_size_upto) {
                    ESP_LOGI(BT_APP_CORE_TAG, "received data len -->> %d", item_size);
                }
                else {
                    if (xSemaphoreTake(s_sig_write_semaphore, portMAX_DELAY)) {
                        int l_sample = 0, r_sample = 0;
                        // 2 channel, FFT_LEN
                        for (int i = 0; i < item_size_upto; i+=4) {
                            l_sample = (uint16_t)(((*(data + i + 1) << 8) | *(data + i)));
                            r_sample = (uint16_t)(((*(data + i + 3) << 8) | *(data + i + 2)));

                            l_data[i>>2] = (float)l_sample;
                            r_data[i>>2] = (float)r_sample;
                        }
                        xSemaphoreGive(s_sig_read_semaphore);
                    }
                    else {
                        ESP_LOGE(BT_APP_CORE_TAG, "missed a frame");
                    }
                }
                // release the ring buffer data
                i2s_channel_write(tx_chan, data, item_size, &bytes_written, portMAX_DELAY);
                vRingbufferReturnItem(s_ringbuf_i2s, (void *)data);
            }
        }
    }
}

static void sig_proc_task_handler(void *arg)
{
    // using internal DAC for fig
    size_t item_written;
    int frame_count = 0;
    ESP_LOGI(BT_APP_CORE_TAG, "sig proc task lanuched");
    if (pdFALSE == xSemaphoreGive(s_sig_write_semaphore)) {
        ESP_LOGE(BT_APP_CORE_TAG, "semphore give failed");
    }

    for (;;) {
        if (xSemaphoreTake(s_sig_read_semaphore, portMAX_DELAY)) {
            frame_count += 1;
            float lavg = 0., ravg = 0.;
            for (int i = 0; i < FFT_LEN; ++i) {
                lavg += l_data[i];
                ravg += r_data[i];
            }
            proc_audio_frame(l_data);

            xSemaphoreGive(s_sig_write_semaphore);

            float lnorm = lavg / FFT_LEN / 65536;
            float rnorm = ravg / FFT_LEN / 65536;
            uint8_t lval = (uint8_t)(lnorm * lnorm * 256); // convert 16 bit to 8 bit
            uint8_t rval = (uint8_t)(rnorm * rnorm * 256);
            if (frame_count == 1000) {
                ESP_LOGI(BT_APP_CORE_TAG, "average value %d, %d", (int)lval, (int)rval);
                frame_count = 0;
            }


            for (int i = 0; i < DAC_LEN; i+=4) {
                dac_buf[i] = 0; // left channel
                dac_buf[i+1] = lval;
                dac_buf[i+2] = 0; // right channel
                dac_buf[i+3] = rval;
            }

            // ESP_LOGI(BT_APP_CORE_TAG, "sig proc consumed a signal");
            dac_continuous_write(sig_chan, dac_buf, DAC_LEN, &item_written, portMAX_DELAY);
        }
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
    ESP_LOGI(BT_APP_CORE_TAG, "ringbuffer data empty! mode changed: RINGBUFFER_MODE_PREFETCHING");
    ringbuffer_mode = RINGBUFFER_MODE_PREFETCHING;
    if ((s_i2s_write_semaphore = xSemaphoreCreateBinary()) == NULL) {
        ESP_LOGE(BT_APP_CORE_TAG, "%s, Semaphore create failed", __func__);
        return;
    }
    if ((s_ringbuf_i2s = xRingbufferCreate(RINGBUF_HIGHEST_WATER_LEVEL, RINGBUF_TYPE_BYTEBUF)) == NULL) {
        ESP_LOGE(BT_APP_CORE_TAG, "%s, ringbuffer create failed", __func__);
        return;
    }

    if ((s_sig_read_semaphore = xSemaphoreCreateBinary()) == NULL) {
        ESP_LOGE(BT_APP_CORE_TAG, "%s, Semaphore create failed", __func__);
        return;
    }

    if ((s_sig_write_semaphore = xSemaphoreCreateBinary()) == NULL) {
        ESP_LOGE(BT_APP_CORE_TAG, "%s, Semaphore create failed", __func__);
        return;
    }

    if ((s_bt_sig_task_queue = xQueueCreate(1, sizeof(int))) == NULL) {
        ESP_LOGE(BT_APP_CORE_TAG, "%s, sig task queue create failed", __func__);
    }
    init_audio_handler();

    // xTaskCreate(bt_i2s_task_handler, "BtI2STask", 2048, NULL, configMAX_PRIORITIES - 3, &s_bt_i2s_task_handle);
    xTaskCreatePinnedToCore(bt_i2s_task_handler, "BtI2STask", 9012, NULL, configMAX_PRIORITIES - 3, &s_bt_i2s_task_handle, 0);
    xTaskCreatePinnedToCore(sig_proc_task_handler, "SigProcTask", 9012, NULL, configMAX_PRIORITIES-4, &s_sig_proc_task_handle, 1);
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
    if (s_i2s_write_semaphore) {
        vSemaphoreDelete(s_i2s_write_semaphore);
        s_i2s_write_semaphore = NULL;
    }

    if (s_sig_proc_task_handle) {
        vTaskDelete(s_sig_proc_task_handle);
        s_sig_proc_task_handle = NULL;
    }
    if (s_bt_sig_task_queue) {
        vQueueDelete(s_bt_sig_task_queue);
        s_bt_sig_task_queue = NULL;
    }
    if (s_sig_read_semaphore) {
        vSemaphoreDelete(s_sig_read_semaphore);
        s_sig_read_semaphore= NULL;
    }
    if (s_sig_write_semaphore) {
        vSemaphoreDelete(s_sig_write_semaphore);
        s_sig_write_semaphore= NULL;
    }
    deinit_audio_handler();
}

size_t write_ringbuf(const uint8_t *data, size_t size)
{
    size_t item_size = 0;
    BaseType_t done = pdFALSE;

    if (ringbuffer_mode == RINGBUFFER_MODE_DROPPING) {
        ESP_LOGW(BT_APP_CORE_TAG, "ringbuffer is full, drop this packet!");
        vRingbufferGetInfo(s_ringbuf_i2s, NULL, NULL, NULL, NULL, &item_size);
        if (item_size <= RINGBUF_PREFETCH_WATER_LEVEL) {
            ESP_LOGI(BT_APP_CORE_TAG, "ringbuffer data decreased! mode changed: RINGBUFFER_MODE_PROCESSING");
            ringbuffer_mode = RINGBUFFER_MODE_PROCESSING;
        }
        return 0;
    }

    done = xRingbufferSend(s_ringbuf_i2s, (void *)data, size, (TickType_t)0);

    if (!done) {
        ESP_LOGW(BT_APP_CORE_TAG, "ringbuffer overflowed, ready to decrease data! mode changed: RINGBUFFER_MODE_DROPPING");
        ringbuffer_mode = RINGBUFFER_MODE_DROPPING;
    }

    if (ringbuffer_mode == RINGBUFFER_MODE_PREFETCHING) {
        vRingbufferGetInfo(s_ringbuf_i2s, NULL, NULL, NULL, NULL, &item_size);
        if (item_size >= RINGBUF_PREFETCH_WATER_LEVEL) {
            ESP_LOGI(BT_APP_CORE_TAG, "ringbuffer data increased! mode changed: RINGBUFFER_MODE_PROCESSING");
            ringbuffer_mode = RINGBUFFER_MODE_PROCESSING;
            if (pdFALSE == xSemaphoreGive(s_i2s_write_semaphore)) {
                ESP_LOGE(BT_APP_CORE_TAG, "semphore give failed");
            }
        }
    }

    return done ? size : 0;
}
