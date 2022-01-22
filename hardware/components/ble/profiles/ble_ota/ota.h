#ifndef _OTA_H
#define _OTA_H

#include <stdint.h>
#include "driver_plf.h"

#define OTA_HDR_RESULT_LEN          1
#define OTA_HDR_OPCODE_LEN          1
#define OTA_HDR_LENGTH_LEN          2
//#define OTA_CRC_CHECK
#ifdef OTA_CRC_CHECK
#define OTA_TIMEOUT  5000
#endif
typedef enum 
{
    OTA_CMD_NVDS_TYPE,
    OTA_CMD_GET_STR_BASE,
    OTA_CMD_READ_FW_VER,    //read firmware version
    OTA_CMD_PAGE_ERASE,
    OTA_CMD_CHIP_ERASE,
    OTA_CMD_WRITE_DATA,
    OTA_CMD_READ_DATA,
    OTA_CMD_WRITE_MEM,
    OTA_CMD_READ_MEM,
    OTA_CMD_REBOOT,
    OTA_CMD_NULL,
}ota_cmd_t;

typedef enum 
{
    OTA_RSP_SUCCESS,
    OTA_RSP_ERROR,
    OTA_RSP_UNKNOWN_CMD,
}ota_rsp_t;

typedef enum 
{
    OTA_NVDS_NONE,
    OTA_NVDS_FLASH,
    OTA_NVDS_EEPROM,
}ota_nvds_type;

#ifdef OTA_CRC_CHECK
typedef enum 
{
    OTA_TIMOUT,
    OTA_ADDR_ERROR,
    OTA_CHECK_FAIL,
}ota_warning_type;
#endif

__PACKED struct firmware_version
{
    uint32_t firmware_version;
}GCC_PACKED;

__PACKED struct storage_baseaddr
{
    uint32_t baseaddr;
}GCC_PACKED;

__PACKED struct page_erase_rsp
{
    uint32_t base_address;
}GCC_PACKED;

__PACKED struct write_mem_rsp
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct read_mem_rsp
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct write_data_rsp
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct read_data_rsp
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct app_ota_rsp_hdr_t
{
    uint8_t result;
    uint8_t org_opcode;
    uint16_t length;
    __PACKED union
    {
        uint8_t nvds_type;
        struct firmware_version version;
        struct storage_baseaddr baseaddr;
        struct page_erase_rsp page_erase;
        struct write_mem_rsp write_mem;
        struct read_mem_rsp read_mem;
        struct write_data_rsp write_data;
        struct read_data_rsp read_data;
    }GCC_PACKED rsp;
}GCC_PACKED;

__PACKED struct page_erase_cmd
{
    uint32_t base_address;
}GCC_PACKED;

__PACKED struct write_mem_cmd
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct read_mem_cmd
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct write_data_cmd
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

__PACKED struct read_data_cmd
{
    uint32_t base_address;
    uint16_t length;
}GCC_PACKED;

#ifdef OTA_CRC_CHECK
__PACKED struct firmware_check
{
    uint32_t firmware_length;
    uint32_t CRC32_data;
}GCC_PACKED;
#endif

__PACKED struct app_ota_cmd_hdr_t
{
    uint8_t opcode;
    uint16_t length;
    __PACKED union
    {
        struct page_erase_cmd page_erase;
        struct write_mem_cmd write_mem;
        struct read_mem_cmd read_mem;
        struct write_data_cmd write_data;
        struct read_data_cmd read_data;
#ifdef OTA_CRC_CHECK		
        struct firmware_check fir_crc_data;
#endif		
    }GCC_PACKED cmd;
}GCC_PACKED;

struct otas_send_rsp
{
    uint8_t conidx;

    uint16_t length;
    uint8_t buffer[];
};

uint8_t app_get_ota_state(void);
void app_set_ota_state(uint8_t state_flag);
void ota_init(uint8_t conidx);
void ota_deinit(uint8_t conidx);
void app_otas_recv_data(uint8_t conidx,uint8_t *p_data,uint16_t len);
uint16_t app_otas_read_data(uint8_t conidx,uint8_t *p_data);

#endif //__OTA_H



