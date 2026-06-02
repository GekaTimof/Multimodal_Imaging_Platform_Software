#ifndef __OPTOSKYSUPPORT
#define __OPTOSKYSUPPORT

#ifdef __cplusplus
extern "C" {
#endif

/******************************************************************************
  VarType define
*******************************************************************************/
typedef unsigned char BOOLEAN;
typedef unsigned char INT_8U;
typedef signed char INT_8S;
typedef unsigned short INT_16U;
typedef signed short INT_16S;
typedef unsigned int INT_32U;
typedef signed int INT_32S;
typedef float FLOAT;
typedef double DOUBLE;

/******************************************************************************
  API of optosky_interface_manager_task
*******************************************************************************/
INT_8S optosky_open_spectrometer(void);
INT_8S optosky_close_spectrometer(void);
INT_8U *optosky_get_library_version(void);

/******************************************************************************
  API of optosky_device_infomation_task
*******************************************************************************/
typedef enum {
    IntegralTime_Size_16 = 0x00,
    IntegralTime_Size_32 = 0x01
}__Attr_Integral_Length;

typedef enum {
    IntegralTime_Unit_ms = 0x00,
    IntegralTime_Unit_us = 0x02,
}__Attr_Integral_Unit;

INT_8S optosky_get_vendor(INT_8S* vendor, INT_8U vendor_size);
INT_8S optosky_get_PN(INT_8S* pn, INT_8U pn_size);
INT_8S optosky_get_SN(INT_8S* sn, INT_8U sn_size);
INT_8S optosky_get_version(INT_8S* version, INT_8U version_size);
INT_8S optosky_get_production_date(INT_8S* date, INT_8U date_size);
__Attr_Integral_Length optosky_get_integral_time_length(void);
__Attr_Integral_Unit optosky_get_integral_time_unit(void);

/******************************************************************************
  API of optosky_device_calibration_task
*******************************************************************************/
INT_16S optosky_get_wavelength_of_the_spec(FLOAT *wavelength ,INT_16U size);

/******************************************************************************
  API of optosky_scanning_spectrum_task
*******************************************************************************/
INT_8S optosky_get_integral_time(INT_32U *scanTime);
INT_8S optosky_set_integral_time(INT_32U scanTime);
INT_8S optosky_set_average(INT_16U average);
INT_16S optosky_acquisition_dark_sync(INT_32U integrationTime, INT_16U *spectrum);
INT_16S optosky_acquisition_spectrum_sync(INT_32U integrationTime, INT_16U *spectrum);
INT_8S optosky_acquisition_dark_async(INT_32U integrationTime);
INT_8S optosky_acquisition_spectrum_async(INT_32U integrationTime);
INT_16S optosky_get_spectrum_data_async(INT_16U *spectrum);

/******************************************************************************
  API of optosky_outside_control_task
*******************************************************************************/
typedef enum {
	GPIO_PIN_0 = 0,
	GPIO_PIN_1,
	GPIO_PIN_2,
	GPIO_PIN_3,
	GPIO_PIN_4,
	GPIO_PIN_5,
	GPIO_PIN_6,
	GPIO_PIN_7,
	GPIO_PIN_8,
	GPIO_PIN_9,
	GPIO_PIN_10,
	GPIO_PIN_11,
}EXT_GPIO_PIN;

typedef enum {
	GPIO_VALUE_ERROR = -1,
	GPIO_VALUE_LOW = 0,
	GPIO_VALUE_HIGH,
}EXT_GPIO_VALUE;

INT_8S optosky_set_external_GPIO_value(EXT_GPIO_PIN num, EXT_GPIO_VALUE value);
INT_8S optosky_external_trigger_enable(INT_16U integrationTime, void(*external_scan_callback)(INT_16U count, INT_16U *spectrum));
INT_8S optosky_external_trigger_disable(void);

#ifdef __cplusplus
}
#endif
#endif

