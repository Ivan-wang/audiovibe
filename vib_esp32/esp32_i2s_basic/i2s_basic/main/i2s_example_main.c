/* I2S Example

    This example code will output 100Hz sine wave and triangle wave to 2-channel of I2S driver
    Every 5 seconds, it will change bits_per_sample [16, 24, 32] for i2s data

    This example code is in the Public Domain (or CC0 licensed, at your option.)

    Unless required by applicable law or agreed to in writing, this
    software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
    CONDITIONS OF ANY KIND, either express or implied.
*/
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2s.h"
#include "driver/gpio.h"
#include "esp_system.h"
#include "esp_check.h"
#include "esp_log.h"


#define SAMPLE_RATE     (48000)
#define I2S_NUM         (1)
#define I2S_BCK_IO      (GPIO_NUM_18)
#define I2S_WS_IO       (GPIO_NUM_5)
#define I2S_DO_IO       (GPIO_NUM_23)
#define I2S_DI_IO       (GPIO_NUM_19)

#define I2S_RX_BUFFER_SIZE 512*2*2
int i2s_rx_buffer[I2S_RX_BUFFER_SIZE];
char I2S_RX_TAG[] = "I2S_RX";

QueueHandle_t i2sQ;
size_t byte_count = 0;
size_t frame_count = 0;

static void i2s_rx_task(void *args) {
    i2s_event_t i2s_event;
    size_t readBytes = 0;
    while (1) {
        if (xQueueReceive(i2sQ, &i2s_event, portMAX_DELAY) == pdPASS) {
            ESP_LOGI(I2S_RX_TAG, "[echo] received a RX done event");
            if (i2s_event.type == I2S_EVENT_RX_DONE) {
                esp_err_t ret = i2s_read(I2S_NUM, i2s_rx_buffer, I2S_RX_BUFFER_SIZE, &readBytes, 0);
                if (ret != ESP_OK) {
                ESP_LOGE(I2S_RX_TAG, "[echo] i2s read failed..");
                }
                else {
                    if (readBytes != 0) {
                        ESP_LOGI(I2S_RX_TAG, "[echo] i2s read successful! (%d bytes)", readBytes);
                        ESP_LOGI(I2S_RX_TAG, "10 BYTE: ");
                        ESP_LOG_BUFFER_HEXDUMP(I2S_RX_TAG, i2s_rx_buffer, 10, ESP_LOG_INFO);
                        byte_count += readBytes;
                        frame_count += 1;
                        ESP_LOGI(I2S_RX_TAG, "Received Byte Count %d", byte_count);
                        ESP_LOGI(I2S_RX_TAG, "Received Frame Count %d", frame_count);
                    }
                }
            }
        }
        else {
            ESP_LOGE(I2S_RX_TAG, "Receive I2S Queue Error");
        }
    }
}

// static void i2s_rx_task(void *args) {
//     while(1) {
//         // vTaskDelay(100 / portTICK_PERIOD_MS);
//         memset(i2s_rx_buffer, 0, I2S_RX_BUFFER_SIZE*sizeof(int));
//         size_t readBytes = 0;
//         esp_err_t ret = i2s_read(I2S_NUM, i2s_rx_buffer, I2S_RX_BUFFER_SIZE, &readBytes, 100/portTICK_PERIOD_MS);
//         if (ret != ESP_OK) {
//             ESP_LOGE(I2S_RX_TAG, "[echo] i2s read failed..");
//         }
//         else {
//             if (readBytes != 0) {
//                 ESP_LOGI(I2S_RX_TAG, "[echo] i2s read successful! (%d bytes)", readBytes);
//                 ESP_LOGI(I2S_RX_TAG, "10 BYTE: ");
//                 ESP_LOG_BUFFER_HEXDUMP(I2S_RX_TAG, i2s_rx_buffer, 10, ESP_LOG_INFO);
//             }
            
//         }
//     }
// }

void app_main(void) 
{
    // i2sQ = xQueueCreate(4, sizeof(i2s_event_t));
    //for 36Khz sample rates, we create 100Hz sine wave, every cycle need 36000/100 = 360 samples (4-bytes or 8-bytes each sample)
    //depend on bits_per_sample
    //using 6 buffers, we need 60-samples per buffer
    //if 2-channels, 16-bit each channel, total buffer is 360*4 = 1440 bytes
    //if 2-channels, 24/32-bit each channel, total buffer is 360*8 = 2880 bytes
    i2s_config_t i2s_config = {
        .mode = I2S_MODE_SLAVE | I2S_MODE_RX,
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = true,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1                                //Interrupt level 1
    };
    i2s_pin_config_t pin_config = {
        .mck_io_num = I2S_PIN_NO_CHANGE,
        .bck_io_num = I2S_BCK_IO,
        .ws_io_num = I2S_WS_IO,
        .data_out_num = I2S_DO_IO,
        .data_in_num = I2S_DI_IO
    };
    i2s_driver_install(I2S_NUM, &i2s_config, 8, &i2sQ);
    i2s_set_pin(I2S_NUM, &pin_config);

    xTaskCreate(i2s_rx_task, "i2s_rx_task", 8192, NULL, 5, NULL);

}
