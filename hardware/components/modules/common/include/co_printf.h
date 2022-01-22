#ifndef _CO_PRINTF_H
#define _CO_PRINTF_H

int co_printf(const char *format, ...);
int co_sprintf(char *out, const char *format, ...);
#define FR_DBG_ON            0x01U
#define FR_DBG_OFF           0x00U
#define FR_LOG(x)   if((x) & FR_DBG_ON) co_printf

#define log_printf(format,...) //co_printf(format,##__VA_ARGS__)

#define SEC_CONN_LOG(format,...) do { \
log_printf("[SEC_CONN]:"); \
log_printf(format,##__VA_ARGS__); \
} while(0)

#define SEC_LOG(format,...) do { \
log_printf("[SEC]:"); \
log_printf(format,##__VA_ARGS__); \
} while(0)


#endif
