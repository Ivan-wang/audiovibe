/**
 * Copyright (c) 2019, Freqchip
 * 
 * All rights reserved.
 * 
 * 
 */

/*
 * INCLUDES
 */
#include "lcd.h"
#include "oledfont.h"
#include "bmp.h"
#include <stdint.h>
#include "sys_utils.h"
#include <string.h>
#include <stdbool.h>
#include "driver_ssp.h"
#include "driver_gpio.h"
#include "driver_iomux.h"
#include "driver_pmu.h"


#define DEV_V_1_4  (1)  //FR8016H DEV1.4
/*
 * MACROS
 */

/*
 * CONSTANTS 
 */

/*
 * TYPEDEFS 
 */

enum
{
    DC_CMD,
    DC_DATA,
};

#define LCD_DC_DATA    gpio_porta_write(gpio_porta_read() | (1<<GPIO_BIT_7) )//gpio_set_pin_value(GPIO_PORT_A, GPIO_BIT_7, 1)
#define LCD_DC_CMD     gpio_porta_write(gpio_porta_read() & ~(1<<GPIO_BIT_7) )// gpio_set_pin_value(GPIO_PORT_A, GPIO_BIT_7, 0)

#define LCD_EN_OFF   pmu_set_led2_value(0)//  gpio_set_pin_value(GPIO_PORT_D, GPIO_BIT_7, 1)
#define LCD_EN_ON    pmu_set_led2_value(1) // gpio_set_pin_value(GPIO_PORT_D, GPIO_BIT_7, 0)

#define LCD_RES_LOW    gpio_porta_write(gpio_porta_read() & ~(1<<GPIO_BIT_0) )// gpio_set_pin_value(GPIO_PORT_A, GPIO_BIT_0, 0)
#define LCD_RES_HIGH   gpio_porta_write(gpio_porta_read() | (1<<GPIO_BIT_0) )// gpio_set_pin_value(GPIO_PORT_A, GPIO_BIT_0, 1)

/*
 * GLOBAL VARIABLES 
 */

uint16_t BACK_COLOR;   //����ɫ
uint8_t dc_value = DC_CMD;   //cmd
uint8_t picture_idx = 0;//ͼƬˢ�����
extern uint8_t led_state;
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
* @fn		LCD_WR_DATA8
*
* @brief	lcd write a byte
*
* @param	data - Written data
*
* @return	None.
*/
__attribute__((section("ram_code"))) void LCD_WR_DATA8(uint8_t data)
{
    if(dc_value==DC_CMD)
    {
        //cpu_delay(10);  //for 48Mhz.  12Mhz mask this
        LCD_DC_DATA;
        dc_value = DC_DATA;
    }
    ssp_send_byte(data);
}

/*********************************************************************
* @fn		LCD_WR_DATA
*
* @brief	lcd Write a 16-bit data
*
* @param	data - Written data
*
* @return	None.
*/
__attribute__((section("ram_code"))) void LCD_WR_DATA(uint16_t data)
{
    if(dc_value==DC_CMD)
    {
        //cpu_delay(10);  //for 48Mhz.  12Mhz mask this
        LCD_DC_DATA;
        dc_value = DC_DATA;
    }
    ssp_send_byte(data>>8);
    ssp_send_byte(data);
}


/*********************************************************************
* @fn		LCD_WR_REG
*
* @brief	Write register
*
* @param	cmd - Written data
*
* @return	None.
*/
__attribute__((section("ram_code"))) void LCD_WR_REG(uint8_t cmd)
{
    if(dc_value==DC_DATA)
    {
        //cpu_delay(10);  //for 48Mhz.  12Mhz mask this
        LCD_DC_CMD;
        dc_value = DC_CMD;
    }
    ssp_send_byte(cmd);
}

/*********************************************************************
* @fn		LCD_Address_Set
*
* @brief	Write register
*
* @param	x1,x2 Set the start and end addresses of a row
*			y1,y2 Set the start and end addresses of a line
*
* @return	None.
*/
void LCD_Address_Set(uint16_t x1,uint16_t y1,uint16_t x2,uint16_t y2)
{
    if(USE_HORIZONTAL==0)
    {
        LCD_WR_REG(0x2a);//�е�ַ����
        LCD_WR_DATA(x1);
        LCD_WR_DATA(x2);
        LCD_WR_REG(0x2b);//�е�ַ����
        LCD_WR_DATA(y1);
        LCD_WR_DATA(y2);
        LCD_WR_REG(0x2c);//������д
    }
    else if(USE_HORIZONTAL==1)
    {
        LCD_WR_REG(0x2a);//�е�ַ����
        LCD_WR_DATA(x1);
        LCD_WR_DATA(x2);
        LCD_WR_REG(0x2b);//�е�ַ����
        LCD_WR_DATA(y1+80);
        LCD_WR_DATA(y2+80);
        LCD_WR_REG(0x2c);//������д
    }
    else if(USE_HORIZONTAL==2)
    {
        LCD_WR_REG(0x2a);//�е�ַ����
        LCD_WR_DATA(x1);
        LCD_WR_DATA(x2);
        LCD_WR_REG(0x2b);//�е�ַ����
        LCD_WR_DATA(y1);
        LCD_WR_DATA(y2);
        LCD_WR_REG(0x2c);//������д
    }
    else
    {
        LCD_WR_REG(0x2a);//�е�ַ����
        LCD_WR_DATA(x1+80);
        LCD_WR_DATA(x2+80);
        LCD_WR_REG(0x2b);//�е�ַ����
        LCD_WR_DATA(y1);
        LCD_WR_DATA(y2);
        LCD_WR_REG(0x2c);//������д
    }
}

/*********************************************************************
* @fn		LCD_DriverDelay
*
* @brief	Delay function
*
* @param	dly   - ms
*
* @return	None.
*/

void LCD_DriverDelay(uint32_t dly)
{
    co_delay_100us(dly*10);
}


/*********************************************************************
* @fn		Lcd_Init
*
* @brief	Initialize lcd
*
* @param	None
*
* @return	None.
*/

void Lcd_Init(void)
{
    system_set_port_mux(GPIO_PORT_A, GPIO_BIT_4, PORTA4_FUNC_SSP0_CLK);
    system_set_port_mux(GPIO_PORT_A, GPIO_BIT_5, PORTA5_FUNC_SSP0_CSN);
    system_set_port_mux(GPIO_PORT_A, GPIO_BIT_6, PORTA6_FUNC_SSP0_DOUT);

    /* working in master mode */
    ssp_init_(8, SSP_FRAME_MOTO, SSP_MASTER_MODE, 24000000, 2, NULL);

    system_set_port_mux(GPIO_PORT_A,GPIO_BIT_0,PORTA0_FUNC_A0);
    system_set_port_mux(GPIO_PORT_A,GPIO_BIT_7,PORTA7_FUNC_A7);
//     system_set_port_mux(GPIO_PORT_D,GPIO_BIT_7,PORTD7_FUNC_D7);

    gpio_set_dir(GPIO_PORT_A, GPIO_BIT_0, GPIO_DIR_OUT);
    gpio_set_dir(GPIO_PORT_A, GPIO_BIT_7, GPIO_DIR_OUT);
//     gpio_set_dir(GPIO_PORT_D, GPIO_BIT_7, GPIO_DIR_OUT);

    system_set_port_pull(GPIO_PA0,true);
    system_set_port_pull(GPIO_PA7,true);
//     system_set_port_pull(GPIO_PD7,true);

    LCD_DC_CMD;
    dc_value = DC_CMD;

    LCD_RES_HIGH;
    LCD_DriverDelay(10);
    LCD_RES_LOW;
    LCD_DriverDelay(10);          //Delay 10ms
    LCD_RES_HIGH;
    LCD_DriverDelay(10);          //Delay 10ms

    LCD_WR_REG(0x11);
    LCD_DriverDelay(120);          //Delay 120ms

#if DEV_V_1_4
    {
	LCD_WR_REG(0xfe);
	LCD_WR_REG(0xef);	
			
	LCD_WR_REG(0x36);	
	LCD_WR_DATA8(0x48);	
	LCD_WR_REG(0x3a);	
	LCD_WR_DATA8(0x05);	


	LCD_WR_REG(0x85);	
	LCD_WR_DATA8(0x80);	
	LCD_WR_REG(0x86);	
	LCD_WR_DATA8(0xf8);
	LCD_WR_REG(0x87);	
	LCD_WR_DATA8(0x79);	
	LCD_WR_REG(0x89);	
	LCD_WR_DATA8(0x13);
		
	LCD_WR_REG(0x8b);	
	LCD_WR_DATA8(0x80);	
		
	LCD_WR_REG(0x8d);	
	LCD_WR_DATA8(0x33);	
	LCD_WR_REG(0x8e);	
	LCD_WR_DATA8(0x8f);	
	LCD_WR_REG(0x8f);	
	LCD_WR_DATA8(0x73);

	//inversion
	LCD_WR_REG(0xe8);
	LCD_WR_DATA8(0x12);
	LCD_WR_DATA8(0x00);	

	LCD_WR_REG(0xec);
	LCD_WR_DATA8(0x13);
	LCD_WR_DATA8(0x02);	
	LCD_WR_DATA8(0x88);	

	//cobD?��?
	LCD_WR_REG(0xbf);	 
	LCD_WR_DATA8(0x1c);		  

	LCD_WR_REG(0xad);	   
	LCD_WR_DATA8(0x4a);

	LCD_WR_REG(0xae);	   
	LCD_WR_DATA8(0x44);

	LCD_WR_REG(0xac);	   
	LCD_WR_DATA8(0x44);
	
	LCD_WR_REG(0xff);
	LCD_WR_DATA8(0x62);
	LCD_WR_REG(0x99);	
	LCD_WR_DATA8(0x3e);
	LCD_WR_REG(0x9d);	
	LCD_WR_DATA8(0x4b);
	LCD_WR_REG(0x98);	
	LCD_WR_DATA8(0x3e);
	LCD_WR_REG(0x9c);	
	LCD_WR_DATA8(0x4b);
	
	LCD_WR_REG(0xc3);	
	LCD_WR_DATA8(0x58);//58

	LCD_WR_REG(0xc4);	
	LCD_WR_DATA8(0x4E);//4E

	LCD_WR_REG(0xc9);	
	LCD_WR_DATA8(0x08);

	LCD_WR_REG(0xf0);
	LCD_WR_DATA8(0x45);
	LCD_WR_DATA8(0x0A);
	LCD_WR_DATA8(0x0A);
	LCD_WR_DATA8(0x06);
	LCD_WR_DATA8(0x05);
	LCD_WR_DATA8(0x2E);

	LCD_WR_REG(0xf2);
	LCD_WR_DATA8(0x45);
	LCD_WR_DATA8(0x09);
	LCD_WR_DATA8(0x0A);
	LCD_WR_DATA8(0x0b);
	LCD_WR_DATA8(0x05);
	LCD_WR_DATA8(0x2E);

	LCD_WR_REG(0xf1);
	LCD_WR_DATA8(0x45);
	LCD_WR_DATA8(0x8F);
	LCD_WR_DATA8(0x8f);
	LCD_WR_DATA8(0x3B);
	LCD_WR_DATA8(0x3F);
	LCD_WR_DATA8(0x7f);

	LCD_WR_REG(0xf3);
	LCD_WR_DATA8(0x45);
	LCD_WR_DATA8(0x8f);
	LCD_WR_DATA8(0x8f);
	LCD_WR_DATA8(0x3B);
	LCD_WR_DATA8(0x3F);
	LCD_WR_DATA8(0x7f);


	LCD_WR_REG(0x11);
	LCD_DriverDelay(120);
	LCD_WR_REG(0x29);
	LCD_WR_REG(0x2c);
}
#else
//************* Start Initial Sequence **********//
    LCD_WR_REG(0x36);
    if(USE_HORIZONTAL==0)LCD_WR_DATA8(0x00);
    else if(USE_HORIZONTAL==1)LCD_WR_DATA8(0xC0);
    else if(USE_HORIZONTAL==2)LCD_WR_DATA8(0x70);
    else LCD_WR_DATA8(0xA0);

    LCD_WR_REG(0x3A);
    LCD_WR_DATA8(0x05);

    LCD_WR_REG(0xB2);
    LCD_WR_DATA8(0x0C);
    LCD_WR_DATA8(0x0C);
    LCD_WR_DATA8(0x00);
    LCD_WR_DATA8(0x33);
    LCD_WR_DATA8(0x33);

    LCD_WR_REG(0xB7);
    LCD_WR_DATA8(0x35);

    LCD_WR_REG(0xBB);
    LCD_WR_DATA8(0x19);

    LCD_WR_REG(0xC0);
    LCD_WR_DATA8(0x2C);

    LCD_WR_REG(0xC2);
    LCD_WR_DATA8(0x01);

    LCD_WR_REG(0xC3);
    LCD_WR_DATA8(0x12);

    LCD_WR_REG(0xC4);
    LCD_WR_DATA8(0x20);

    LCD_WR_REG(0xC6);
    LCD_WR_DATA8(0x0F);

    LCD_WR_REG(0xD0);
    LCD_WR_DATA8(0xA4);
    LCD_WR_DATA8(0xA1);

    LCD_WR_REG(0xE0);
    LCD_WR_DATA8(0xD0);
    LCD_WR_DATA8(0x04);
    LCD_WR_DATA8(0x0D);
    LCD_WR_DATA8(0x11);
    LCD_WR_DATA8(0x13);
    LCD_WR_DATA8(0x2B);
    LCD_WR_DATA8(0x3F);
    LCD_WR_DATA8(0x54);
    LCD_WR_DATA8(0x4C);
    LCD_WR_DATA8(0x18);
    LCD_WR_DATA8(0x0D);
    LCD_WR_DATA8(0x0B);
    LCD_WR_DATA8(0x1F);
    LCD_WR_DATA8(0x23);

    LCD_WR_REG(0xE1);
    LCD_WR_DATA8(0xD0);
    LCD_WR_DATA8(0x04);
    LCD_WR_DATA8(0x0C);
    LCD_WR_DATA8(0x11);
    LCD_WR_DATA8(0x13);
    LCD_WR_DATA8(0x2C);
    LCD_WR_DATA8(0x3F);
    LCD_WR_DATA8(0x44);
    LCD_WR_DATA8(0x51);
    LCD_WR_DATA8(0x2F);
    LCD_WR_DATA8(0x1F);
    LCD_WR_DATA8(0x1F);
    LCD_WR_DATA8(0x20);
    LCD_WR_DATA8(0x23);

    LCD_WR_REG(0x21);

    LCD_WR_REG(0x11);
//Delay (120);

    LCD_WR_REG(0x29);
#endif    
    LCD_EN_ON;
}



/*********************************************************************
* @fn		LCD_Clear
*
* @brief	clear screen
*
* @param	Color   - Color after clearing screen
*
* @return	None.
*/

void LCD_Clear(uint16_t Color)
{
	uint16_t i,j;
	   LCD_Address_Set(0,0,LCD_W-1,LCD_H-1);
	   for(i=0; i<LCD_W; i++)
	   {
		   for (j=0; j<LCD_H; j++)
		   {
			   LCD_WR_DATA(Color);
		   }
	
	   }


}



/*********************************************************************
* @fn		LCD_ShowChinese
*
* @brief	Display Chinese Characters
*
* @param	x,y	  - Starting coordinates
*			index - Chinese Character Number
*           size  - Font size
*           color - color
* @return	None.
*/

void LCD_ShowChinese(uint16_t x,uint16_t y,uint8_t index,uint8_t size,uint16_t color)
{
    uint8_t i,j;
    uint8_t *temp,size1;
    if(size==16)
    {
        temp=Hzk16;   //ѡ���ֺ�
    }
    if(size==32)
    {
        temp=Hzk32;
    }
    LCD_Address_Set(x,y,x+size-1,y+size-1); //����һ�����ֵ�����
    size1=size*size/8;//һ��������ռ���ֽ�
    temp+=index*size1;//д�����ʼλ��
    for(j=0; j<size1; j++)
    {
        for(i=0; i<8; i++)
        {
            if((*temp&(1<<i))!=0)//�����ݵĵ�λ��ʼ��
            {
                LCD_WR_DATA(color);//����
            }
            else
            {
                LCD_WR_DATA(BACK_COLOR);//������
            }
        }
        temp++;
    }
}


/*********************************************************************
* @fn		LCD_DrawPoint
*
* @brief	Draw points
*
* @param	x,y	  - Starting coordinates
*           color - color
* @return	None.
*/

void LCD_DrawPoint(uint16_t x,uint16_t y,uint16_t color)
{
    LCD_Address_Set(x,y,x,y);//���ù��λ��
    LCD_WR_DATA(color);
}


/*********************************************************************
* @fn		LCD_DrawPoint_big
*
* @brief	Draw big points
*
* @param	x,y	  - Starting coordinates
*           color - color
* @return	None.
*/

void LCD_DrawPoint_big(uint16_t x,uint16_t y,uint16_t color)
{
    LCD_Fill(x-1,y-1,x+1,y+1,color);
}



/*********************************************************************
* @fn		LCD_Fill
*
* @brief	Full screen fill
*
* @param	xsta,xend Set the start and end addresses of a row
*			ysta,yend Set the start and end addresses of a line
*           color - fill color
* @return	None.
*/

void LCD_Fill(uint16_t xsta,uint16_t ysta,uint16_t xend,uint16_t yend,uint16_t color)
{
    uint16_t i,j;
    LCD_Address_Set(xsta,ysta,xend,yend);      //���ù��λ��
    for(i=ysta; i<=yend; i++)
    {
        for(j=xsta; j<=xend; j++)LCD_WR_DATA(color); //���ù��λ��
    }
}


/*********************************************************************
* @fn		LCD_DrawLine
*
* @brief	Draw a straight line
*
* @param	x1,x2 Set the start and end addresses of a row
*			y1,y2 Set the start and end addresses of a line
*           color -  color
* @return	None.
*/

void LCD_DrawLine(uint16_t x1,uint16_t y1,uint16_t x2,uint16_t y2,uint16_t color)
{
    uint16_t t;
    int xerr=0,yerr=0,delta_x,delta_y,distance;
    int incx,incy,uRow,uCol;
    delta_x=x2-x1; //������������
    delta_y=y2-y1;
    uRow=x1;//�����������
    uCol=y1;
    if(delta_x>0)incx=1; //���õ�������
    else if (delta_x==0)incx=0;//��ֱ��
    else
    {
        incx=-1;
        delta_x=-delta_x;
    }
    if(delta_y>0)incy=1;
    else if (delta_y==0)incy=0;//ˮƽ��
    else
    {
        incy=-1;
        delta_y=-delta_x;
    }
    if(delta_x>delta_y)distance=delta_x; //ѡȡ��������������
    else distance=delta_y;
    for(t=0; t<distance+1; t++)
    {
        LCD_DrawPoint(uRow,uCol,color);//����
        xerr+=delta_x;
        yerr+=delta_y;
        if(xerr>distance)
        {
            xerr-=distance;
            uRow+=incx;
        }
        if(yerr>distance)
        {
            yerr-=distance;
            uCol+=incy;
        }
    }
}


/*********************************************************************
* @fn		LCD_DrawRectangle
*
* @brief	Draw a rectangle
*
* @param	x1,x2 Set the start and end addresses of a row
*			y1,y2 Set the start and end addresses of a line
*           color -  color
* @return	None.
*/
void LCD_DrawRectangle(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2,uint16_t color)
{
    LCD_DrawLine(x1,y1,x2,y1,color);
    LCD_DrawLine(x1,y1,x1,y2,color);
    LCD_DrawLine(x1,y2,x2,y2,color);
    LCD_DrawLine(x2,y1,x2,y2,color);
}


/*********************************************************************
* @fn		Draw_Circle
*
* @brief	Draw a Circle
*
* @param	x0,y0 - Set the center point
*			r     - Circle radius
*			color -  color
* @return	None.
*/
void Draw_Circle(uint16_t x0,uint16_t y0,uint8_t r,uint16_t color)
{
    int a,b;
    a=0;
    b=r;
    while(a<=b)
    {
        LCD_DrawPoint(x0-b,y0-a,color);             //3
        LCD_DrawPoint(x0+b,y0-a,color);             //0
        LCD_DrawPoint(x0-a,y0+b,color);             //1
        LCD_DrawPoint(x0-a,y0-b,color);             //2
        LCD_DrawPoint(x0+b,y0+a,color);             //4
        LCD_DrawPoint(x0+a,y0-b,color);             //5
        LCD_DrawPoint(x0+a,y0+b,color);             //6
        LCD_DrawPoint(x0-b,y0+a,color);             //7
        a++;
        if((a*a+b*b)>(r*r))//�ж�Ҫ���ĵ��Ƿ��Զ
        {
            b--;
        }
    }
}


/*********************************************************************
* @fn		LCD_ShowChar
*
* @brief	Display character
*
* @param	x,y - Set the Starting coordinates
*			num	  - Number of characters
*			mode -  1: Overlay 0: Non-overlapping
*           color - color
* @return	None.
*/
void LCD_ShowChar(uint16_t x,uint16_t y,uint8_t num,uint8_t mode,uint16_t color)
{
    uint8_t temp;
    uint8_t pos,t;
    uint16_t x0=x;
    if(x>LCD_W-16||y>LCD_H-16)return;       //���ô���
    num=num-' ';//�õ�ƫ�ƺ��ֵ
    LCD_Address_Set(x,y,x+8-1,y+16-1);      //���ù��λ��
    if(!mode) //�ǵ��ӷ�ʽ
    {
        for(pos=0; pos<16; pos++)
        {
            temp=asc2_1608[(uint16_t)num*16+pos];        //����1608����
            for(t=0; t<8; t++)
            {
                if(temp&0x01)LCD_WR_DATA(color);
                else LCD_WR_DATA(BACK_COLOR);
                temp>>=1;
                x++;
            }
            x=x0;
            y++;
        }
    }
    else //���ӷ�ʽ
    {
        for(pos=0; pos<16; pos++)
        {
            temp=asc2_1608[(uint16_t)num*16+pos];        //����1608����
            for(t=0; t<8; t++)
            {
                if(temp&0x01)LCD_DrawPoint(x+t,y+pos,color);//��һ����
                temp>>=1;
            }
        }
    }
}




/*********************************************************************
* @fn		LCD_ShowString
*
* @brief	Display string
*
* @param	x,y - Set the Starting coordinates
*			p   - String pointer
*			color - color
* @return	None.
*/

void LCD_ShowString(uint16_t x,uint16_t y,const uint8_t *p,uint16_t color)
{
    while(*p!='\0')
    {
        if(x>LCD_W-16)
        {
            x=0;
            y+=16;
        }
        if(y>LCD_H-16)
        {
            y=x=0;
            LCD_Clear(RED);
        }
        LCD_ShowChar(x,y,*p,0,color);
        x+=8;
        p++;
    }
}

/*********************************************************************
* @fn		LCD_DriverWriteDataBuf
*
* @brief	Write buffer to lcd
*
* @param	buf - data buffer
*			len	- data len
* @return	None.
*/
__attribute__((section("ram_code"))) void LCD_DriverWriteDataBuf(uint8_t *buf, uint32_t len)
{
    if(dc_value==DC_CMD)
    {
        //cpu_delay(10);  //for 48Mhz.  12Mhz mask this
        LCD_DC_DATA;
        dc_value = DC_DATA;
    }
    if((uint32_t)buf> 0x20000000)     //it is from ram
        ssp_send_data(buf,len);
    else    //from flash
    {
        uint32_t pos = 0;
        while(pos < len)
        {
            if( (len-pos) >=120)
            {
                ssp_send_120Bytes(buf+pos);       //80 ontime
                pos+=120;
            }
            else
            {
                //ssp_send_bytes(buf,len-pos);
                ssp_send_data(buf,len-pos);
                pos = len;
            }
        }
    }
}

/*********************************************************************
* @fn		LCD_Clear_quick
*
* @brief	Clear the display quickly
*
* @param	Color - Color
*			
* @return	None.
*/
void LCD_Clear_quick(uint16_t Color)
{

	uint16_t i;
    uint16_t lcd_buf[240];
	Color = (Color << 8) | (Color >> 8);
	for(i = 0;i < 240; i++)
		lcd_buf[i] = Color;
    LCD_Address_Set(0,0,LCD_W-1,LCD_H-1);
    for(i = 0; i < 240; i++)
    {
        LCD_DriverWriteDataBuf((uint8_t *)lcd_buf, 480);
    }
}


/*********************************************************************
* @fn		lcd_show_logo
*
* @brief	Display logo and working mode
*
* @param	mode_str - a string for the name of the working mode
*			
* @return	None.
*/
void lcd_show_logo(const uint8_t*  mode_str)
{
	uint8_t LCD_ShowStringBuff[30] = {0};
	BACK_COLOR=WHITE;
	LCD_Clear(WHITE);
	LCD_ShowChinese(10+TITLE_OFFSET,20,0,32,BLUE);   //��
	LCD_ShowChinese(85+TITLE_OFFSET,20,1,32,BLUE);   //��
	LCD_ShowChinese(160+TITLE_OFFSET,20,2,32,BLUE);   //��

	sprintf((char *)LCD_ShowStringBuff,"Mode:");
	LCD_ShowString(5,75,LCD_ShowStringBuff,BLACK);
	LCD_ShowString(50, 75, mode_str, BLACK);
	

}

/*********************************************************************
* @fn		demo_LCD_APP
*
* @brief	Initialize lcd, Display logo and working mode
*
* @param	None
*			
* @return	None.
*/

#ifdef MULTILINK
#include "ble_multi_con.h"
void multicon_LCD_APP(void)
{
    
    Lcd_Init();
	if(dev_info.node_role == DEV_ROL_SLAVE){
        BACK_COLOR=RED;
        LCD_Clear_quick(BACK_COLOR);
    }else{
        BACK_COLOR=BLUE;
        LCD_Clear_quick(BACK_COLOR);
    }  
    

    //lcd_show_mul_con();    
}

void lcd_show_mul_con(void)
{
	uint8_t LCD_ShowStringBuff[30] = {0};
	//co_printf("lcd_show_mul_con\r\n");
    if(led_state){
        sprintf((char *)LCD_ShowStringBuff,"led:%d  ",led_state);
	    LCD_ShowString(5,15,LCD_ShowStringBuff,YELLOW);
        LCD_Fill(80,15,180,34,YELLOW);
    }else{
        sprintf((char *)LCD_ShowStringBuff,"led:%d  ",led_state);
	    LCD_ShowString(5,15,LCD_ShowStringBuff,BLACK);
        LCD_Fill(80,15,180,34,BLACK);
    }

    sprintf((char *)LCD_ShowStringBuff,"Node_id:%d  ",dev_info.node_id);
	LCD_ShowString(5,35,LCD_ShowStringBuff,YELLOW);
    uint32_t slave_id = dev_info.dev_node_info.node_info.slave_id;
    sprintf((char *)LCD_ShowStringBuff,"layer:%d    layer_ID:%x%x%x%x%x ",dev_info.dev_node_info.node_info.layer,(slave_id>>(4*4))&0xf,(slave_id>>(3*4))&0xf,(slave_id>>(2*4))&0xf,(slave_id>>(1*4))&0xf,(slave_id)&0xf);
	LCD_ShowString(5,55,LCD_ShowStringBuff,YELLOW);
    sprintf((char *)LCD_ShowStringBuff,"M1:%d M2:%d    slave_num:%d ",dev_info.dev_node_info.node_info.Master1_state ,dev_info.dev_node_info.node_info.Master2_state,dev_info.dev_node_info.node_info.slave_num);
	LCD_ShowString(5,75,LCD_ShowStringBuff,YELLOW);

    if(dev_info.dev_node_info.node_info.layer == 0){
	    LCD_ShowString(5,95,"off_line ",BLACK );
        LCD_Fill(5,110,40,145,BLACK);
    }else{
	    LCD_ShowString(5,95,"on_line  ",YELLOW);
        LCD_Fill(5,110,40,145,YELLOW);
    }
	

}
#else

void demo_LCD_APP(void)
{
    
    Lcd_Init();
	LCD_DisPIC(picture_idx++);     
}

#include "ie2.h"
#define LCD_MAX_ROW     240
#define LCD_MAX_COLUMN  240
#define LCD_MAX_COLUMN_X2  480
static uint8_t lcd_buf[LCD_MAX_COLUMN_X2];
static void get_char_lcd_buff_from_point_array(uint8_t point_byte,uint8_t *buff,uint8_t color,uint8_t bg_color)
{
    uint8_t i=8;
    do
    {
        i--;
        if( point_byte & BIT(i) )
        {
            *(buff + ((7-i) <<1) ) = color;
            *(buff + ((7-i) <<1) + 1) = color;
        }
        else
        {
            *(buff + ((7-i)<<1) ) = bg_color;
            *(buff + ((7-i)<<1) + 1) = bg_color;
        }
    }
    while(i > 0);
}
#define MOD(x,y)  ( (x%y)?(x/y+1):(x/y) )
void LCD_DisBWPic(uint8_t pos_x,uint8_t pos_y,uint8_t len_x,uint8_t len_y,uint8_t *image_arr,uint8_t color,uint8_t bg_color)
{
	  uint8_t i=0;
    uint8_t byte_idx_x = 0;
    uint32_t offset = 0;
	
    uint8_t byte_num_x = MOD(len_x,8);
	  uint8_t *data_x;
    for(i = 0; i<len_y ; i++)
    {
				data_x = &image_arr[offset];
				offset += byte_num_x;
        byte_idx_x = 0;
        while(byte_idx_x < byte_num_x)
        {
            get_char_lcd_buff_from_point_array(data_x[byte_idx_x], lcd_buf + (byte_idx_x << 4),color,bg_color);
            byte_idx_x++;
        }
        LCD_DriverWriteDataBuf(lcd_buf, len_x<<1);
    }
}
/*********************************************************************
* @fn		LCD_DisPIC
*
* @brief	Display a picture with a resolution of 240x240
*
* @param	pic_idx - The serial number of the picture
*			
* @return	None.
*/
void LCD_DisPIC(uint8_t pic_idx)
{
	LCD_Address_Set(0, 0, 240-1, 240-1);
	if(pic_idx == 0){
			LCD_DriverWriteDataBuf((uint8_t *)( gImage_logo240x240), 480*240);
	}else if(pic_idx == 1){
		LCD_DriverWriteDataBuf((uint8_t *)( gImage_erweima240x240), 480*240);
	}else if(pic_idx == 2){
		//LCD_Clear_quick(RED);
		LCD_DisBWPic(0, 0, 240, 240,(uint8_t *)&gImage_ie2[0],0x55,0x00);
	}else if(pic_idx == 3){
		LCD_Clear_quick(GREEN);
	}else if(pic_idx == 4){
		LCD_Clear_quick(BLUE);
	}
  
}
#endif


