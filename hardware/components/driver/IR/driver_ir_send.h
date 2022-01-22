#ifndef _DRIVER_IR_SEND_H
#define _DRIVER_IR_SEND_H
#include <stdint.h>
#include <stdbool.h>


#define IRLEADLOW     9000     //������
#define IRLEADHIGHT   4500

#define IRLOGIC0LOW   560      //0
#define IRLOGIC0HIGHT 560

#define IRLOGIC1LOW    560     //1
#define IRLOGIC1HIGHT  1680

#define IRSTOPLOW    600        //ֹͣλ
#define IRSTOPHIGHT     13930+500 //ֹͣ��־λ����   Ҳ�Ǻ���ѧϰ���ж�Ϊֹͣλ��ʱ�䳤��

#define IR_CF_36K   36000
#define IR_CF_38K   38000
#define IR_CF_56K   56000



#define IR_CARRIER_FRE       IR_CF_38K


#define IR_SLEEP_EN 1  //ϵͳ����sleep������£���Ҫ���ú궨��Ϊ1��������Ϊ0
#define LERANDATABUFMAX 3000
#define LERANDATACNTMAX 200


//���ⷢ�Ͳ����ṹ��
typedef struct
{
    uint8_t IR_Busy;//IR ����busy
    uint8_t IR_pwm_state;//��Ϊ1����Ϊ0
    uint8_t IR_pwm_Num;//IR �����ͼ��
    uint8_t IR_pwm_SendNum;//IR �ѷ��ͼ��
    uint32_t IR_Pwm_State_Date[LERANDATACNTMAX];//���潫�������ת�ɶ�ʱʱ�������
    uint32_t ir_carrier_fre;//�ز�Ƶ��
    uint32_t total_count;//pwm total_count
    uint32_t high_count_half;//pwm high_count
    bool loop;//IR�Ƿ�ѭ������ true:ѭ������ false:���η���
} TYPEDEFIRPWMTIM;

extern TYPEDEFIRPWMTIM IR_PWM_TIM;

//����ѧϰ������ݽ���ṹ��
typedef struct
{
    uint8_t IR_learn_state;//IR ѧϰ״̬��bit0:0��δѧϰ�� 1����ѧϰ;  bit1 1:ѧϰ��,0:����ѧϰ��
    uint32_t ir_learn_Date[LERANDATACNTMAX];//���潫����ѧϰ����ʱ�������浽�������У�����ֱ�ӷ���
    uint8_t ir_learn_data_cnt;//ѧϰ�������
    uint32_t ir_carrier_fre;//�ز�Ƶ��
} TYPEDEFIRLEARNDATA;
extern TYPEDEFIRLEARNDATA ir_learn_data;

//����ѧϰ��صĽṹ��
typedef struct
{
    uint8_t ir_learn_step;//IRѧϰ����
    uint32_t ir_carrier_fre;//�ز�Ƶ��
    uint8_t ir_carrier_cycle;//�ز�����
    uint8_t ir_learn_start;//1:һ��ʼ 0��δ��ʼ
    uint16_t ir_carrier_times;//�ز�����
    uint16_t ir_timer_cnt;//��ʱ������
//  uint8_t ir_learn_data_cnt;//ѧϰ�������
//  uint32_t ir_learn_Date[100];//�������ѧϰ�ļ��
    uint32_t ir_learn_data_buf[LERANDATABUFMAX];//ir����������
    uint16_t ir_learn_data_buf_cnt;//ir�������������
    uint32_t ir_learn_Date[LERANDATACNTMAX];//���潫����ѧϰ����ʱ�������浽�������У�����ֱ�ӷ���
    uint8_t ir_learn_data_cnt;//ѧϰ�������
    uint32_t ir_carrier_cycle_data[6];//�ز�Ƶ�����ݻ���
    uint8_t ir_carrier_cycle_data_cnt;//�ز�Ƶ�����ݻ������
} TYPEDEFIRLEARN;
//extern TYPEDEFIRLEARN ir_learn;

enum IR_LEARN_STEP
{
    //IR_LEARN_GET_CARRIER,
    IR_WAIT_STOP,
    IR_LEARN_GET_DATA,
};

enum IR_MODE
{
    IR_SEND,
    IR_LEARN,
};

/*
1 refer to IR_test_demo0() to send ir value.
2 In Func IR_start_send() &  IR_task_func() to port IR enable & stop pins
3 In func IR_start_learn() & IR_stop_learn() to port IR learn exti isr.
4 Port IR learn pin for below marco:
    #define IR_LEARN_PIN_INIT() 
    #define IR_LEARN_DISENABLE()
    #define IR_LEARN_ENABLE()
*/
void IR_decode(uint8_t *ir_data,uint8_t data_size,TYPEDEFIRPWMTIM *IR_Send_struct);
void IR_start_send(TYPEDEFIRPWMTIM *IR_Send_struct);
void IR_init(void);
void IR_stop_send(void);

uint8_t IR_start_learn(void);
void IR_stop_learn(void);


/*
1 only send ir value, follow IR_test_demo0();
2 learn a ir value from another controller, follow IR_test_demo1(); After call it, 5s timers later, learn stop
    during learn coures, if  IR_learn_state =ir_data_check() in timer0_isr_ram(), IR_learn_state = true. learn is successful.
3 If you want to resend what has been learn in IR_test_demo1(),  call IR_test_demo2() to resend it.
*/
void IR_test_demo0(void);
void IR_test_demo1(void);
void IR_test_demo2(void);

#endif

