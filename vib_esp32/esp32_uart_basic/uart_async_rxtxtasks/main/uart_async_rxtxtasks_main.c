/* UART asynchronous example, that uses separate RX and TX tasks

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "driver/uart.h"
#include "string.h"
#include "driver/gpio.h"

#define TX_BUF_SIZE 512
#define RX_BUF_SIZE 512
static char txBuffer[TX_BUF_SIZE+1];
static char rxBuffer[RX_BUF_SIZE+1];

#define TXD_PIN (GPIO_NUM_17)
#define RXD_PIN (GPIO_NUM_16)

// enum UART_ENGINE_STATE {IDLE, SEND_READY, REC_INCOMING, REC_READY, SHUT_DOWN};
// enum UART_ENGINE_STATE state = IDLE;

enum MAIN_ENGINE_STATE {INIT, IDLE, BT_AUDIO_SETUP, BT_AUDIO_READY, CHECK_UART, ERROR};
enum MAIN_ENGINE_STATE main_state = INIT;
enum MAIN_ENGINE_STATE prev_state = INIT;

char TX_TASK_TAG[] = "TX_TASK";
char RX_TASK_TAG[] = "RX_TASK";
char ENG_TASK_TAG[] = "ENG_TASK";

void init(void) {
    const uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };
    // We won't use a buffer for sending data.
    uart_driver_install(UART_NUM_1, RX_BUF_SIZE * 2, 0, 0, NULL, 0);
    uart_param_config(UART_NUM_1, &uart_config);
    uart_set_pin(UART_NUM_1, TXD_PIN, RXD_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);


}

int send_data(const char* data)
{
    const int len = strlen(data);
    const int txBytes = uart_write_bytes(UART_NUM_1, data, len);
    ESP_LOGI(TX_TASK_TAG, "Wrote %d bytes", txBytes);
    return txBytes;
}

int receive_data(void) {
    const int rxBytes = uart_read_bytes(UART_NUM_1, rxBuffer, RX_BUF_SIZE, 1000 / portTICK_RATE_MS);
    if (rxBytes > 0){
        rxBuffer[rxBytes] = 0;
        ESP_LOGI(RX_TASK_TAG, "Read %d bytes: '%s'", rxBytes, rxBuffer);
        ESP_LOG_BUFFER_HEXDUMP(RX_TASK_TAG, rxBuffer, rxBytes, ESP_LOG_INFO);
    }
    for (int i = 0; i < rxBytes; ++i) {
        if (rxBuffer[i] == 'O' && rxBuffer[i+1] == 'K') {
            return 1;
        }
    }
    return 0;
}

int is_uart_return_ok(void) {
    const int len = strlen(rxBuffer);
    for (int i = 0; i < len; ++i) {
        if (rxBuffer[i] == 'O' && rxBuffer[i+1] == 'K') {
            return 1;
        }
    }
    return 0;
}

static void run_main_engine(void *arg) {
    while (1) {
        vTaskDelay(100 / portTICK_PERIOD_MS);
        switch (main_state)
        {
        case INIT: {
            send_data("AT\r\n");
            prev_state = INIT;
            main_state = CHECK_UART;
            continue;
        }
        case BT_AUDIO_SETUP: {
            send_data("AT+PROFILE=160\r\n");
            prev_state = main_state;
            main_state = CHECK_UART;
            continue;
        }
        case BT_AUDIO_READY: {
            ESP_LOGI(ENG_TASK_TAG, "BT_AUDIO_READY...");
            prev_state = main_state;
            main_state = IDLE;
            continue;
        }
        case CHECK_UART: {
            if (receive_data()) {
                if (prev_state == INIT) { main_state = BT_AUDIO_SETUP; }
                else if (prev_state == BT_AUDIO_SETUP) { main_state = BT_AUDIO_READY; }
                ESP_LOGI(ENG_TASK_TAG, "UART CHECK OK...");
            }
            else {
                if (prev_state == IDLE) { main_state = IDLE; }
                else { main_state = INIT; }
                ESP_LOGI(ENG_TASK_TAG, "UART CHECK FAILED...");
            }
            continue;
        }
        case IDLE: {
            prev_state = main_state;
            main_state = CHECK_UART;
            continue;
        }
        default:
            break;
        }
    }
}

// static void run_uart_engine(void *arg) {
//     char TX_TASK_TAG[] = "TX_TASK";
//     char RX_TASK_TAG[] = "RX_TASK";
//     char ENG_TASK_TAG[] = "ENG_TASK";
//     esp_log_level_set(RX_TASK_TAG, ESP_LOG_INFO);
//     while (1) {
//         vTaskDelay(100 / portTICK_PERIOD_MS);
//         switch (state)
//         {
//         case IDLE: {
//             ESP_LOGI(ENG_TASK_TAG, "Engine IDLE...\n");
//             continue; // continue the loop, run another switch...
//         }
//         case SEND_READY: {
//             int len = strlen(txBuffer);
//             int txBytes = uart_write_bytes(UART_NUM_1, txBuffer, len);
//             ESP_LOGI(TX_TASK_TAG, "Wrote %d bytes", txBytes);
//             state = REC_INCOMING;
//             continue;
//         }
//         case REC_INCOMING: {
//             const int rxBytes = uart_read_bytes(UART_NUM_1, rxBuffer, RX_BUF_SIZE, 1000 / portTICK_RATE_MS);
//             if (rxBytes > 0) {
//                 rxBuffer[rxBytes] = 0;
//                 ESP_LOGI(RX_TASK_TAG, "Read %d bytes: '%s'", rxBytes, rxBuffer);
//                 ESP_LOG_BUFFER_HEXDUMP(RX_TASK_TAG, rxBuffer, rxBytes, ESP_LOG_INFO);
//                 state = REC_READY;
//             }
//             else {
//                 ESP_LOGI(RX_TASK_TAG, "No Msg Received");
//             }
//             continue;
//         }
//         case REC_READY:
//             continue;
//         case SHUT_DOWN:
//             break;
//         default:
//             continue;
//         }
//         break;
//     }
// }

// static void tx_task(void *arg)
// {
//     // char *SEND_TASK_TAG = "SEND_CMD_TASK";
//     // esp_log_level_set(TX_TASK_TAG, ESP_LOG_INFO);
//     while (1) {
//         if (state == IDLE) {
//             strcpy(txBuffer, "AT\r\n");
//             state = SEND_READY;
//             // ESP_LOGI(SEND_TASK_TAG, "Wrote %d bytes", );
//         }
//         // sendData(TX_TASK_TAG, "AT+PROFILE\r\n");
//         vTaskDelay(2000 / portTICK_PERIOD_MS);
//     }
// }

// static void rx_task(void *arg)
// {
//     char *CHECK_TASK_TAG = "CHECK_TASK";
//     // esp_log_level_set(RX_TASK_TAG, ESP_LOG_INFO);
//     // uint8_t* data = (uint8_t*) malloc(RX_BUF_SIZE+1);
//     while (1) {
//         if (state == REC_READY) {
//             if (is_uart_return_ok()) {
//                 ESP_LOGI(CHECK_TASK_TAG, "CHECK REC OK!");
//             }
//             else {
//                 ESP_LOGI(CHECK_TASK_TAG, "CHECK REC ERROR!");
//             }
//             state = IDLE;
//         }
//         vTaskDelay(2000 / portTICK_PERIOD_MS);
//     }
//     // free(data);
// }

void app_main(void)
{
    init();
    // xTaskCreate(run_uart_engine, "uart_engine", 1024*2, NULL, 10, NULL);
    // xTaskCreate(rx_task, "uart_rx_task", 1024*2, NULL, 10, NULL);
    // xTaskCreate(tx_task, "uart_tx_task", 1024*2, NULL, 10, NULL);
    xTaskCreate(run_main_engine, "main_engine", 1024*2, NULL, 10, NULL);
}
