/*
   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/

#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include "freertos/xtensa_api.h"
#include "freertos/FreeRTOSConfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "bt_app_core.h"
#include "driver/i2s.h"
#include "freertos/ringbuf.h"

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

static xQueueHandle s_bt_app_task_queue = NULL;  /* handle of work queue */
static xTaskHandle s_bt_app_task_handle = NULL;  /* handle of application task  */
static xTaskHandle s_bt_i2s_task_handle = NULL;  /* handle of I2S task */
static xTaskHandle s_bt_vib_task_handle = NULL; /* handle of pwm task */
static RingbufHandle_t s_ringbuf_i2s = NULL;     /* handle of ringbuffer for I2S */
static RingbufHandle_t s_ringbuf_i2s_vib = NULL;

/*******************************
 * STATIC FUNCTION DEFINITIONS
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

    for (;;) {
        /* receive data from ringbuffer and write it to I2S DMA transmit buffer */
        data = (uint8_t *)xRingbufferReceive(s_ringbuf_i2s, &item_size, (portTickType)portMAX_DELAY);
        if (item_size != 0){
            i2s_write(1, data, item_size, &bytes_written, portMAX_DELAY);
            vRingbufferReturnItem(s_ringbuf_i2s, (void *)data);
        }
    }
}

static void audio2vibration(uint8_t *out, size_t out_len, const int16_t *lchannel, const int16_t *rchannel, size_t channel_len)
{
    float *f_lchannel = (float *)malloc(channel_len*sizeof(float));
    float *f_rchannel = (float *)malloc(channel_len*sizeof(float));
    float lavg = 0.0, ravg = 0.0;

    for (size_t i = 0; i < channel_len; ++i) {
        lavg += abs((float)lchannel[i]);
        ravg += abs((float)rchannel[i]);
    }

    lavg /= (float)channel_len;
    ravg /= (float)channel_len;

    ESP_LOGI(BT_APP_CORE_TAG, "AVG_POWER: L:[%.4f] - R[%.4f]", lavg, ravg);

    uint8_t llevel = 0;
    uint8_t rlevel = 0;

    for (size_t i = 0; i < out_len / 4; i += 4) {
        out[i] = llevel;
        out[i+1] = rlevel;
    }

    return;
}

static void bt_vib_task_handler(void *arg)
{
    uint8_t *data = NULL;
    size_t item_size = 0;
    size_t vib_item_size = 0;
    const size_t i2s_len = 512;
    const size_t i2s_len_bytes = i2s_len * 2 * sizeof(int16_t);
    const size_t vib_len = 24;
    const size_t vib_len_bytes = vib_len * 2 * sizeof(uint8_t);

    int16_t lchannel[i2s_len];
    int16_t rchannel[i2s_len]; 
    memset(lchannel, 0, sizeof(int16_t)*i2s_len);
    memset(rchannel, 0, sizeof(int16_t)*i2s_len);

    uint8_t vibdata[vib_len*2]; // [left, right]
    memset(vibdata, 0, vib_len_bytes);
    size_t count = 0;
    for (;;) {
        data = (uint8_t *)xRingbufferReceiveUpTo(s_ringbuf_i2s_vib, &item_size, (portTickType)portMAX_DELAY, i2s_len_bytes);
        if (item_size > 0) {
            // if received, processing then return
            if (item_size == i2s_len_bytes) {
                // copy data
                for (size_t b = 0; b < i2s_len_bytes; b += 4) {
                    lchannel[b>>2] = (((lchannel[b>>2] | data[b+1]) << 8) | data[b]);
                    rchannel[b>>2] = (((rchannel[b>>2] | data[b+3]) << 8) | data[b+2]);
                }

                vRingbufferReturnItem(s_ringbuf_i2s_vib, (void *)data);

                audio2vibration(vibdata, vib_len_bytes, lchannel, rchannel, i2s_len);

                // write to i2s DMA
                i2s_write(0, vibdata, vib_len_bytes, &vib_item_size, portMAX_DELAY);

                // clean up
                // memset(lchannel, 0, sizeof(int16_t)*i2s_len);
                // memset(rchannel, 0, sizeof(int16_t)*i2s_len);
                // memset(vibdata, 0, vib_len_bytes);

                count += 1;
                if (count == 200) {
                    ESP_LOGI(BT_APP_CORE_TAG, "Processed 200 Frames");
                    count = 0;
                }
            }
            else{
                // otherwise return immediately
                vRingbufferReturnItem(s_ringbuf_i2s_vib, (void *)data);
            }
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
    if ((s_ringbuf_i2s = xRingbufferCreate(8 * 1024, RINGBUF_TYPE_BYTEBUF)) == NULL) {
        return;
    }

    if ((s_ringbuf_i2s_vib = xRingbufferCreate(8 * 1024, RINGBUF_TYPE_BYTEBUF)) == NULL) {
        vRingbufferDelete(s_ringbuf_i2s); // if failed, free i2s ringbuf
        return;
    }
    // create heavy audio task on core 1, and other tasks to core 0
    xTaskCreatePinnedToCore(bt_i2s_task_handler, "BtI2STask", 1024, NULL, configMAX_PRIORITIES - 10, &s_bt_i2s_task_handle, 0);
    xTaskCreatePinnedToCore(bt_vib_task_handler, "BtI2SVibTask", 9012, NULL, configMAX_PRIORITIES - 9, &s_bt_vib_task_handle, 1);
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
    if (s_bt_vib_task_handle) {
        vTaskDelete(s_bt_vib_task_handle);
        s_bt_vib_task_handle = NULL;
    }

    if (s_ringbuf_i2s_vib) {
        vRingbufferDelete(s_ringbuf_i2s_vib);
        s_ringbuf_i2s_vib= NULL;
    }
}

size_t write_ringbuf(const uint8_t *data, size_t size)
{
    BaseType_t done = xRingbufferSend(s_ringbuf_i2s, (void *)data, size, (portTickType)portMAX_DELAY);

    return done ? size : 0;
}

size_t write_ringbuf_vib(const uint8_t *data, size_t size)
{
    BaseType_t done = xRingbufferSend(s_ringbuf_i2s_vib, (void *)data, size, (portTickType)portMAX_DELAY);

    return done ? size : 0;
}
