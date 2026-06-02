#ifndef __OPTOSKY_SUPPORT_MANA
#define __OPTOSKY_SUPPORT_MANA

#include "libusb.h"
#include "list.h"

//#define OPTOSKY_LIB_VERION  "V1.0.0"  /* 支持光谱仪基本功能,仅支持连接单台设备 First verion.*/
//#define OPTOSKY_LIB_VERION  "V2.0"    /* 支持连接多台设备             20210218. By Zhengshy*/
//#define OPTOSKY_LIB_VERION  "V2.1"    /* 添加自动积分时间功能 20210305. By Zhengshy.*/
//#define OPTOSKY_LIB_VERION  "V2.2"    /* 添加Library Initialize and release, free memory 20210518. By LH.*/
//#define OPTOSKY_LIB_VERION  "V2.3"      /* optosky_spectrum_control_resp_msg.pixel_length asign value 20210602. By LH.*/
//#define OPTOSKY_LIB_VERION  "V2.4"      /* add get tec temperature API 20220225. By lilz.*/
//#define OPTOSKY_LIB_VERION  "V2.5"      /* add get device's soft version and modify the length of device's SN(0x10) 20220721 By lilz.*/
//#define OPTOSKY_LIB_VERION  "V2.6" 	  /*增加新的函数，函数功能与原有函数保持一致，但声明形式改为与windows下一致 20231220. By LQ*/
#define OPTOSKY_LIB_VERION  "V2.7" 		/*添加获取波形校正系数，获取非线性校正系数，获取暗电流校正系数功能 20240425. By LQ*/

#define OPTOSKY_USB_VID     (0x0483)    /* OPTOSKY USB-IF vender ID. */
#define OPTOSKY_USB_PID     (0x6666)    /* OPTOSKY USB-IF product ID. */

#define SPEC_NUMBER_MAX 10

#define BULK_ENDPOINT_OUT 0x01
#define BULK_ENDPOINT_IN  0x81

#define INTEGRAL_SIZE_MASK	0x01
#define INTEGRAL_UNIT_MASK	0x02
#define CHECKSUM_BIT_MASK	0x03

typedef enum {
	Include_CheckBit = 0x00,
	Without_CheckBit
}__Attr_CheckBit;

typedef struct{
    INT_8U integral_size;   /* 积分时间长度 */
    INT_8U integral_unit;   /* 积分时间单位 */
    INT_8U checkSum_type;   /* 校验和 */
    INT_16U pixel_number;   /* 像素点个数 */
}__Spec_attributes;

typedef struct{
	INT_8S dev_model[10];	    /* 设备型号. */
	INT_8U serial_number[128];	/* 序列号 */
	__Spec_attributes attributes;	/* 设备属性 */
}__Spec_Info;

typedef struct {
    libusb_device_handle *usbHandler;	/* libusb handler. */
    INT_8S usb_serial[128]; /* usb serial number */
	__Spec_Info specInfo;	/* 设备信息 */
	INT_16U integralTime;	/* 积分时间 */
  __Integral_Time_Mode integralMode;  /* 积分时间设定模式 */
	//FLOAT wavelengthBuf[4096];	/* 波长数组 */
	BOOLEAN externFlag;	    /* 外部触发标志 */
	//INT_16U rawDataBuf[4096];   /* 光谱原始数据 */
	BOOLEAN isOpen;	        /* 激活状态位 */
    struct list_head node;
    pthread_t pth_external;
    void (*External_scan_callback)(__Spectrometer_Handle spec_handle, INT_16U count, INT_16U *spectrum);
}__Optosky_Spec;

__Optosky_Spec *get_spec_control_by_spec_handle(__Spectrometer_Handle spec_handle);
__Spectrometer_Handle get_spec_handle_by_spec_control(__Optosky_Spec optoskySpec);
INT_8S optosky_get_attributes(__Spec_attributes *attributes);
INT_8S optosky_get_specified_dev_attributes(__Spectrometer_Handle spec_handle, __Spec_attributes *attributes);

#endif
