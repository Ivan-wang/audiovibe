/**
 * Copyright (c) 2019, Freqchip
 *
 * All rights reserved.
 *
 *
 */
#ifndef _DRIVER_SYSTEM_H
#define _DRIVER_SYSTEM_H

/*
 * INCLUDES 
 */
#include <stdint.h>
#include <stdbool.h>

#include "driver_iomux.h"
#include "driver_plf.h"
/*
 * MACROS 
 */

/*
 * CONSTANTS 
 */
#define SYSTEM_PORT_MUX_MSK     0xF
#define SYSTEM_PORT_MUX_LEN     4

#define SYSTEM_ONKEY_MAP_EXI11_POS  CO_BIT(7)
#define SYSTEM_ONKEY_MAP_EXI10_POS  CO_BIT(6)
#define SYSTEM_ONKEY_MAP_EXI9_POS   CO_BIT(5)
#define SYSTEM_ONKEY_MAP_EXI8_POS   CO_BIT(4)
#define SYSTEM_ONKEY_MAP_EXI3_POS   CO_BIT(3)
#define SYSTEM_ONKEY_MAP_EXI2_POS   CO_BIT(2)
#define SYSTEM_ONKEY_MAP_EXI1_POS   CO_BIT(1)
#define SYSTEM_ONKEY_MAP_EXI0_POS   CO_BIT(0)

typedef int32_t  s32;
typedef int16_t s16;
typedef int8_t  s8;

typedef const int32_t sc32;  /*!< Read Only */
typedef const int16_t sc16;  /*!< Read Only */
typedef const int8_t sc8;   /*!< Read Only */

typedef __IO int32_t  vs32;
typedef __IO int16_t  vs16;
typedef __IO int8_t   vs8;

typedef __I int32_t vsc32;  /*!< Read Only */
typedef __I int16_t vsc16;  /*!< Read Only */
typedef __I int8_t vsc8;   /*!< Read Only */

typedef uint32_t  u32;
typedef uint16_t u16;
typedef uint8_t  u8;

typedef const uint32_t uc32;  /*!< Read Only */
typedef const uint16_t uc16;  /*!< Read Only */
typedef const uint8_t uc8;   /*!< Read Only */

typedef __IO uint32_t  vu32;
typedef __IO uint16_t vu16;
typedef __IO uint8_t  vu8;

typedef __I uint32_t vuc32;  /*!< Read Only */
typedef __I uint16_t vuc16;  /*!< Read Only */
typedef __I uint8_t vuc8;   /*!< Read Only */

/*
 * TYPEDEFS 
 */
struct system_osc_pll_cfg_t
{
    uint32_t bg_pd:1;
    uint32_t osc_pd:1;
    uint32_t osc_32k_pd:1;
    uint32_t clk_12m_enn:1;
    uint32_t clk_oscX2_enn:1;
    uint32_t clk_bb_enn:1;
    uint32_t clk_adc_enn:1;
    uint32_t rfpll_refclk_enn:1;
    uint32_t reserved:8;
    uint32_t irq_wkup_gate:16;
};

enum system_clk_t
{
    SYSTEM_SYS_CLK_6M,
    SYSTEM_SYS_CLK_12M,
    SYSTEM_SYS_CLK_24M,
    SYSTEM_SYS_CLK_48M,
};

struct system_clk_cfg_t
{
    uint32_t sys_clk_sel:2;
    uint32_t mdm_clk_sel:2;
    uint32_t out_clk_sel:1;
    uint32_t reserved0:3;
    uint32_t clk_out_div:8;
    uint32_t reserved1:16;
};

struct system_clk_enable_t
{
    uint32_t uart0_clk_en:1;
    uint32_t uart1_clk_en:1;
    uint32_t mm_clk_en:1;
    uint32_t trng_clk_en:1;
    uint32_t gpio_clk_en:1;
    uint32_t out_clk_en:1;
    uint32_t cdc_clk_en:1;
    uint32_t qspi_ref_clk_en:1;
    uint32_t efuse_clk_en:1;
    uint32_t reserved:23;
};

struct system_rst_t
{
    uint32_t bb_mas_rst:1;
    uint32_t bb_cry_soft_rst:1;
    uint32_t mm_soft_rst:1;
    uint32_t mm_reg_soft_rst:1;
    uint32_t auxadc_soft_rst:1;
    uint32_t cdc_soft_rst:1;
    uint32_t pdm_soft_rst:1;
    uint32_t qspi_ref_soft_rst:1;
    uint32_t trng_soft_rst:1;
    uint32_t efuse_soft_rst:1;
    uint32_t reserved:22;
};

struct system_codec_mode_t
{
    uint32_t codec_mode:1;  //0: use external codec, 1: use internal codec
    uint32_t mdm_if_sel:1;
    uint32_t fll_cfg_hw:1;
    uint32_t fll_cfg_cpu:1;
    uint32_t mdm_dyn_rrst:1;
    uint32_t mdm_dyn_trst:1;
    uint32_t reserved:26;
};

struct system_led_cntl_t
{
    uint32_t led0_en:1;
    uint32_t led1_en:1;
    uint32_t led2_en:1;
    uint32_t led3_en:1;
    uint32_t led4_en:1;
    uint32_t led0_inv:1;
    uint32_t led1_inv:1;
    uint32_t led2_inv:1;
    uint32_t led3_inv:1;
    uint32_t led4_inv:1;
    uint32_t led_clk_div:6;
    uint32_t reserved:16;
};

struct system_led_cfg_t
{
    uint32_t led_shift:24;
    uint32_t led_low_cnt:8;
};

struct system_charger_state_t
{
    uint32_t bat_qs_data:3;
    uint32_t reserved1:1;
    uint32_t bat_state:1;
    uint32_t reserved2:3;
    uint32_t charger_state:1;
    uint32_t reserved3:23;
};

struct system_keyscan_ctrl_t
{
    uint32_t int_en:1;
    uint32_t reserved:31;
};

struct system_regs_t
{
    struct system_osc_pll_cfg_t osc_pll_cfg;            //0x00
    struct system_clk_cfg_t clk_cfg;                    //0x04
    struct system_clk_enable_t clk_gate;                //0x08
    struct system_rst_t rst;                            //0x0c
    struct system_codec_mode_t codec_mode;              //0x10
    uint32_t remap_virtual_addr;                        //0x14
    uint32_t remap_length;                              //0x18
    uint32_t remap_physical_addr;                       //0x1c
    uint32_t port_pull;                                 //0x20
    uint32_t qspi_pull;                                 //0x24
    uint32_t port_mux[4];                               //0x28
    uint32_t ext_int_mux;                               //0x38
    uint32_t reserved2[7];
    struct system_charger_state_t charger_state;        //0x58
    uint32_t reserved3;
    uint32_t key_scan_value[5];                         //0x60
    struct system_keyscan_ctrl_t key_scan_ctrl;
};

enum rf_tx_power_t {
    RF_TX_POWER_NEG_16dBm,
    RF_TX_POWER_NEG_10dBm,
    RF_TX_POWER_NEG_7dBm,
    RF_TX_POWER_NEG_5dBm,
    RF_TX_POWER_NEG_3dBm,
    RF_TX_POWER_NEG_2dBm,
    RF_TX_POWER_NEG_1dBm,
    RF_TX_POWER_0dBm,
    RF_TX_POWER_POS_1dBm,
    RF_TX_POWER_POS_2dBm,
    RF_TX_POWER_POS_3dBm,
    RF_TX_POWER_POS_4dBm,
    RF_TX_POWER_POS_5dBm,
    RF_TX_POWER_POS_6dBm,
    RF_TX_POWER_POS_7dBm,
    RF_TX_POWER_POS_8dBm,
    RF_TX_POWER_POS_9dBm,
    RF_TX_POWER_POS_10dBm,
    RF_TX_POWER_MAX,
};

/*
 * GLOBAL VARIABLES 
 */
extern volatile struct system_regs_t *const system_regs;

/*
 * LOCAL VARIABLES 
 */

/*
 * LOCAL FUNCTIONS 
 */

/*
 * EXTERN FUNCTIONS 
 */

/*
 * PUBLIC FUNCTIONS 
 */

/*********************************************************************
 * @fn      system_get_pclk
 *
 * @brief   get current system clock, the value should be 12M, 24M, 48M.
 *
 * @param   None
 *
 * @return  current system clock.
 */
uint32_t system_get_pclk(void);

/*********************************************************************
 * @fn      system_set_pclk
 *
 * @brief   change current system clock, some peripheral clock settings need
 *          to be reconfig if neccessary.
 *
 * @param   clk - @ref system_clk_t
 *
 * @return  None.
 */
void system_set_pclk(uint8_t clk);

/*********************************************************************
 * @fn      system_get_pclk_config
 *
 * @brief   get current system clock configuration.
 *
 * @param   None
 *
 * @return  current system clock setting, @ref system_clk_t.
 */
uint8_t system_get_pclk_config(void);

/*********************************************************************
 * @fn      system_set_port_pull
 *
 * @brief   set pull-up of IOs which are controlled by main digital core,
 *          only effect the pull state of IOs indicated by port parameter.
 *          example usage:
 *          system_set_port_pull((GPIO_PA0 | GPIO_PA1), true)
 *
 * @param   port    - each bit represents one GPIO channel
 *          flag    - true: enable pull-up, false: disable pull-up.
 *
 * @return  None.
 */
void system_set_port_pull(uint32_t port, uint8_t pull);

/*********************************************************************
 * @fn      system_set_port_mux
 *
 * @brief   set function of IO which is controlled by main digital core,
 *          example usage:
 *          system_set_port_mux(GPIO_PORT_A, GPIO_BIT_0, PMU_PORT_MUX_KEYSCAN)
 *
 * @param   port    - which group the io belongs to, @ref system_port_t
 *          bit     - the channel number, @ref system_port_bit_t
 *          func    - such as PORTA0_FUNC_I2C0_CLK, PORTA3_FUNC_PDM_DAT
 *
 * @return  None.
 */
void system_set_port_mux(enum system_port_t port, enum system_port_bit_t bit, uint8_t func);

/*********************************************************************
 * @fn      system_sleep_enable
 *
 * @brief   enable system enter deep sleep mode when all conditions are satisfied.
 *
 * @param   None.
 *
 * @return  None.
 */
void system_sleep_enable(void);

/*********************************************************************
 * @fn      system_sleep_disable
 *
 * @brief   disable system enter deep sleep mode.
 *
 * @param   None.
 *
 * @return  None.
 */
void system_sleep_disable(void);

/*********************************************************************
 * @fn      system_set_conn_sleep_max_during
 *
 * @brief   used to set max sleep time when connection is established.
 *
 * @param   during_10ms - max sleep timer, unit: 10ms.
 *
 * @return  None.
 */
void system_set_conn_sleep_max_during(uint32_t during_10ms);

/*********************************************************************
 * @fn      system_latency_enable
 *
 * @brief   reenable latency of connection indicated by conidx.
 *
 * @param   conidx  - connection index, 0xff means latency of all connections
 *                    should be reenabled.
 *
 * @return  None.
 */
void system_latency_enable(uint8_t conidx);

/*********************************************************************
 * @fn      system_latency_disable
 *
 * @brief   disable latency of connection indicated by conidx.
 *
 * @param   conidx  - connection index, 0xff means latency of all connections
 *                    should be disabled.
 *
 * @return  None.
 */
void system_latency_disable(uint8_t conidx);

/*********************************************************************
 * @fn      system_get_curr_time
 *
 * @brief   get how many milliseconds have passed after system start-up,
 *          and the value will loop back to 0 after reaching 858993456.
 *
 * @param   None.
 *
 * @return  None.
 */
uint32_t system_get_curr_time(void);

/*********************************************************************
 * @fn      platform_reset_patch
 *
 * @brief   Re-boot FW.
 *
 * This function is used to re-boot the FW when error has been detected, it is the end of
 * the current FW execution.
 * After waiting transfers on UART to be finished, and storing the information that
 * FW has re-booted by itself in a non-loaded area, the FW restart by branching at FW
 * entry point.
 *
 * @param   error      Error detected by FW
 *
 * @return  None.
 */
void platform_reset_patch(uint32_t error);

/*********************************************************************
 * @fn      system_power_off
 *
 * @brief   put the system into power off mode, GPIO or pmu interrupt can 
 *          power on system according user configurations.
 *
 * @param   aldo_bypass - set aldo working in bypass true save more power.
 *                        suggest user enable this function if power supply
 *                        is less than 3.3v.
 *
 * @return  None.
 */
void system_power_off(bool aldo_bypass);

/*********************************************************************
 * @fn      system_set_tx_power
 *
 * @brief   set RF tx power, increase power means more power consumption
 *
 * @param   tx_power    - tx power configuration, @ref rf_tx_power_t.
 *
 * @return  None.
 */
void system_set_tx_power(enum rf_tx_power_t tx_power);

/*********************************************************************
 * @fn      system_lvd_protect_handle
 *
 * @brief   Protection measures are maded when device in low power state.
 *
 * @param   None.
 *
 * @return  None.
 */
void system_lvd_protect_handle(void);

/*********************************************************************
 * @fn      system_optimize_power_consumption_set, this function has to
 *          be called in function user_custom_parameters.
 *
 * @brief   used to enable or disable power consumption strategy.
 *
 * @param   en  - 1: enable, 0: disable. Default value is disable.
 *
 * @return  None.
 */
void system_optimize_power_consumption_set(uint8_t en);

/*********************************************************************
 * @fn      system_optimize_power_consumption_get
 *
 * @brief   get power consumption strategy status.
 *
 * @param   None.
 *
 * @return  1: enable, 0: disable.
 */
uint8_t system_optimize_power_consumption_get(void);

#endif // _DRIVER_IOMUX_H

