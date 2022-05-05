#include <esp_bt_main.h>
#include <esp_bt_device.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// -------------- Configure --------------------
#include <RingBuf.h>

#define UINT8_DATA

#ifdef UINT8_DATA
const int PWM_RESOLUTION = 8;
const int PWM_MAX_DC = 255;
#else
const int PWM_RESOLUTION = 12;
const int PWM_MAX_DC = 4095;
#endif
// --------------- Data Structure --------------
// requires installing RingBuffer lib (by Locoduino)

// HACK: use RTOS Ring Buffer

// buffer size:  100 vibration frame
const int buf_frame_num = 128;
// elements in one frame: 24
const int frame_size = 24;
using VibrationBuffer = RingBuf<uint16_t, buf_frame_num*frame_size>;
// RingBuf<uint16_t, buf_frame_num*frame_size> buffer;
VibrationBuffer buffer;

//// ----------- PWM Controls (with ledc lib) ----------
const int pwmPin = 16;  // use red LED
const int pwmFreq = 10000; // PWM freq, 10kHz
const int pwmChannel = 0;
const int resolution = PWM_RESOLUTION;

void init_pwm(void) {
   ledcSetup(pwmChannel, pwmFreq, resolution);
   ledcAttachPin(pwmPin, pwmChannel);
}

// --------- Vibration Playing (INT. Based) ----------
hw_timer_t *vibrationTimer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR timerISR(void) {
    portENTER_CRITICAL_ISR(&timerMux);
    if (!buffer.isEmpty()) {
        uint16_t val = 0;
        buffer.lockedPop(val);
        ledcWrite(pwmChannel, int(val));
    }
    else {
       ledcWrite(pwmChannel, PWM_MAX_DC);
    }
    portEXIT_CRITICAL_ISR(&timerMux);
}

void init_vibration_clock(void) {
   vibrationTimer = timerBegin(1, 80, true); // timer precision: 1us
   timerAttachInterrupt(vibrationTimer, &timerISR, true);
   timerAlarmWrite(vibrationTimer, 483, true); // interrupt interval: 483us
   // timerAlarmEnable(vibrationTimer); // do not enable alarm here
}

// ------------------- BTLE Controls ----------------
BLEServer *pServer = NULL;
BLECharacteristic * pTxCharacteristic;
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint8_t txValue = 0;
 
// See the following for generating UUIDs:
// https://www.uuidgenerator.net/
 
#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" // UART service UUID
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
 
void show_ble_addr(void) {
  const uint8_t* point = esp_bt_dev_get_address();
  Serial.print("BTLE Device Addr -> ");
  for (int i = 0; i < 6; ++i) {
    char str[3];
    sprintf(str, "%02X", (int)point[i]);
    Serial.print(str);
    if (i < 5) { Serial.print(":"); }
  }
  Serial.println("");
}

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        timerAlarmEnable(vibrationTimer);
    };
 
    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        timerAlarmDisable(vibrationTimer);
    }
};

class VibrationBufferCallback: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        uint8_t *rxValue = pCharacteristic->getData();
        int m_type = int(
          (rxValue[0]) | (rxValue[1] << 8) | (rxValue[2] << 16) | (rxValue[3] << 24)
        );
        int m_len = int(
          (rxValue[4]) | (rxValue[5] << 8) | (rxValue[6] << 16) | (rxValue[7] << 24)
        );
        Serial.print("********* Received Msg, Type: ");
        Serial.print(std::to_string(m_type).c_str());
        Serial.println("*********");
        Serial.print("********* Received Msg, Data Len: ");
        Serial.print(std::to_string(m_len).c_str());
        Serial.println("*********");
        if (m_type == 0) {
            for (int i = 0; i < m_len; i+=2) {
                uint16_t val = uint16_t((rxValue[i+8]) | (rxValue[i+9] << 8));
//                Serial.print(std::to_string(int(val)).c_str());
//                Serial.print(" ");
                if (!buffer.push(val)) {
                  Serial.println("Failed to push value");
                }
            }
        }
        else {
              buffer.clear();
        }
        Serial.println("");
        
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        uint8_t *rxValue = pCharacteristic->getData();
        int m_type = int(
            (rxValue[0]) | (rxValue[1] << 8) | (rxValue[2] << 16) | (rxValue[3] << 24)
        );
        Serial.print("********* Received Msg, Type: ");
        Serial.print(std::to_string(m_type).c_str());
        Serial.println("*********");

        int m_len = int(
            (rxValue[4]) | (rxValue[5] << 8) | (rxValue[6] << 16) | (rxValue[7] << 24)
        );
        Serial.print("********* Received Msg, Data Len: ");
        Serial.print(std::to_string(m_len).c_str());
        Serial.println("*********");
        
        if (m_len > 0) {
            Serial.print("Received Value (the first 10 number): ");
            for (int i = 0; i < m_len; i=i+2) {
                uint16_t val = uint16_t((rxValue[i+8]) | (rxValue[i+9] << 8));
                Serial.print(std::to_string(int(val)).c_str());
                Serial.print(" ");
            }
            Serial.println();
        }
        else {
            Serial.println("No Data in this Frame");
        }
    }
};
 
void init_ble_server(void) {
    // Create the BLE Device
    BLEDevice::init("UART Service For ESP32");

    // Create the BLE Server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create the BLE Service
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Create a BLE Characteristic
    pTxCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID_TX,
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pTxCharacteristic->addDescriptor(new BLE2902());
 
    BLECharacteristic * pRxCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID_RX,
        BLECharacteristic::PROPERTY_WRITE
        );
 
    //  pRxCharacteristic->setCallbacks(new MyCallbacks());
    pRxCharacteristic->setCallbacks(new VibrationBufferCallback());

    // Start the service
    pService->start();
}

void setup() {
    Serial.begin(115200);
    
    init_pwm();
    init_ble_server();
    init_vibration_clock();

    // Start advertising
    if (pServer != NULL) {
        pServer->getAdvertising()->start();
        Serial.println("Waiting a client connection to notify...");
        show_ble_addr();
    }
    ledcWrite(pwmChannel, PWM_MAX_DC);
}
 
void loop() {
 
//    if (deviceConnected) {
//        pTxCharacteristic->setValue(&txValue, 1);
//        pTxCharacteristic->notify();
//        txValue++;
//        delay(10); // bluetooth stack will go into congestion, if too many packets are sent
//    }
 
    // disconnecting
    if (!deviceConnected && oldDeviceConnected) {
        delay(500); // give the bluetooth stack the chance to get things ready
        pServer->startAdvertising(); // restart advertising
        Serial.println("start advertising");
        oldDeviceConnected = deviceConnected;
    }
    // connecting
    if (deviceConnected && !oldDeviceConnected) {
        // do stuff here on connecting
        oldDeviceConnected = deviceConnected;
    }
}
