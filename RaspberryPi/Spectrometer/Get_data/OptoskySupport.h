#ifndef __OPTOSKYSUPPORT
#define __OPTOSKYSUPPORT

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

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

int optosky_speed_test_handler(INT_32U scanTime);

/******************************************************************************
  API of optosky_interface_manager_task
*******************************************************************************/
typedef struct {
    INT_8S sn[128];
}__Spectrometer_Handle; /* spectrometer handle (user space) */

typedef struct DarkFactor
{
	float k;
	float b;
}s_DARK_FACTOR;

INT_8U *optosky_get_library_version(void);  /* Get library version. */
INT_8U optosky_get_device_list(__Spectrometer_Handle *spec_handle);     /* Gets a list of spectrometer devices. */

/////////////////////// Initialize and release resourec ////////////////////////////
INT_8S optosky_initialize(void);
void optosky_release(void);

/////////////////////// Single Spectrometer Control Function ///////////////////////
INT_8S optosky_open_spectrometer(void);     /* Open the spectrometer. */
INT_8S optosky_close_spectrometer(void);    /* Close the spectrometer. */
bool openSpectraMeter();                    /* Open the spectrometer. This function declaration is the same as the windows version*/
bool closeSpectraMeter();                   /* Close the spectrometer. This function declaration is the same as the windows version*/

/////////////////////// Multiple Spectrometers Control Function ///////////////////////
INT_8S optosky_open_specified_spectrometer(__Spectrometer_Handle spec_handle);  /* Open the specified spectrometer with the spec_handle. */
INT_8S optosky_close_specified_spectrometer(__Spectrometer_Handle spec_handle); /* Close the specified spectrometer with the spec_handle. */
INT_8S optosky_open_all_spectrometer(__Spectrometer_Handle *spec_handle);   /* Turn on all spectrometers. */
INT_8S optosky_close_all_spectrometer(void);    /* Turn off all spectrometers. */


/******************************************************************************
  API of optosky_device_infomation_task
*******************************************************************************/
typedef enum {
    IntegralTime_Size_16 = 0x00,
    IntegralTime_Size_32
}__Attr_Integral_Length;    /* Integral time length. */

typedef enum {
    IntegralTime_Unit_ms = 0x00,
    IntegralTime_Unit_us
}__Attr_Integral_Unit;      /* Integral time unit. */

/////////////////////// Single Spectrometer Control Function ///////////////////////
INT_8S optosky_get_vendor(INT_8S* vendor, INT_8U vendor_size);  /* Get the spectrometer vendor. */
INT_8S optosky_get_PN(INT_8S* pn, INT_8U pn_size);      /* Get the spectrometer PN number. */
INT_8S optosky_get_SN(INT_8S* sn, INT_8U sn_size);      /* Get the spectrometer SN number. */
INT_8S optosky_get_version(INT_8S* version, INT_8U version_size);   /* Get the spectrometer version. */
INT_8S optosky_get_soft_version(INT_8S* version, INT_8U version_size);   /* Get the MCU's version. */
INT_8S optosky_get_production_date(INT_8S* date, INT_8U date_size); /* Get the spectrometer production date. */
__Attr_Integral_Length optosky_get_integral_time_length(void);  /* Get the spectrometer integration time length. */
__Attr_Integral_Unit optosky_get_integral_time_unit(void);  /* Get the spectrometer integration time unit. */
INT_16U optosky_get_pixel_length(void);  /* Get the spectrometer pixel length. */
INT_8S optosky_get_TEC_temperature(INT_8S* temperature, INT_8U temperature_size);/* Get the spectrometer tec temperature */
int getPixelCount();  /*Get the spectrometer pixel count. This function declaration is the same as the windows version*/

/////////////////////// Multiple Spectrometers Control Function ///////////////////////
INT_8S optosky_get_specified_dev_vendor(__Spectrometer_Handle spec_handle, INT_8S* vendor, INT_8U vendor_size);
INT_8S optosky_get_specified_dev_PN(__Spectrometer_Handle spec_handle, INT_8S* pn, INT_8U pn_size);
INT_8S optosky_get_specified_dev_SN(__Spectrometer_Handle spec_handle, INT_8S* sn, INT_8U sn_size);
INT_8S optosky_get_specified_dev_version(__Spectrometer_Handle spec_handle, INT_8S* version, INT_8U version_size);
INT_8S optosky_get_specified_soft_version(__Spectrometer_Handle spec_handle, INT_8S* version, INT_8U version_size);
INT_8S optosky_get_specified_dev_production_date(__Spectrometer_Handle spec_handle, INT_8S* date, INT_8U date_size);
__Attr_Integral_Length optosky_get_specified_dev_integral_time_length(__Spectrometer_Handle spec_handle);
__Attr_Integral_Unit optosky_get_specified_dev_integral_time_unit(__Spectrometer_Handle spec_handle);
INT_16U optosky_get_specified_dev_pixel_length(__Spectrometer_Handle spec_handle);
INT_8S optosky_specified_dev_get_TEC_temperature(__Spectrometer_Handle spec_handle, \
                                                 INT_8S* temperature, INT_8U temperature_size);/* Get the spectrometer tec temperature */

/******************************************************************************
  API of optosky_device_calibration_task
*******************************************************************************/
/////////////////////// Single Spectrometer Control Function ///////////////////////
INT_16S optosky_get_wavelength_of_the_spec(FLOAT *wavelength ,INT_16U size);    /* Get the spectrometer wavelength. */
INT_16S optosky_get_nonlinearity_coefficient(FLOAT *NonlinearityBuf);     /* Get the spectrometer nonlinearity coefficients. */
INT_16S optosky_get_shape_coefficient(FLOAT *ShapeBuf);                   /* Get the spectrometer shape coefficients. */
INT_16S optosky_get_dark_coefficient(s_DARK_FACTOR *DarkBuf);             /* Get the spectrometer dark coefficients. */
INT_8S dataProcess(INT_16U *original_data, FLOAT *dataProcessed, INT_16U spectrum_size, bool isDeductDark, bool isNonlinearCorrect, bool isShapeCalibration, s_DARK_FACTOR *dkcoefficient, FLOAT *nlcoefficient, FLOAT *spcoefficient, INT_32U integrationTime);/*Get the processed spectrometer data.  */

/////////////////////// Multiple Spectrometers Control Function ///////////////////////
INT_16S optosky_get_specified_dev_wavelength_of_the_spec(__Spectrometer_Handle spec_handle, FLOAT *wavelength ,INT_16U size);


/******************************************************************************
  API of optosky_scanning_spectrum_task
*******************************************************************************/
typedef enum {
    IntegralTime_Automatic_Disable = 0,
    IntegralTime_Automatic_Enable
}__Integral_Time_Mode;

/////////////////////// Single Spectrometer Control Function ///////////////////////
INT_8S optosky_get_integral_time(INT_32U *scanTime);    /* Get the spectrometer integration time. */
INT_8S optosky_set_integral_time(INT_32U scanTime);     /* Set the spectrometer integration time. */
INT_8S optosky_set_average(INT_16U average);        /* Set the spectrometer average times */
INT_8S optosky_integral_time_automatic(__Integral_Time_Mode mode);  /* Automatic integration time.This feature is only valid with optosky_acquisition_spectrum_sync functions.*/
INT_16S optosky_acquisition_dark_sync(INT_32U integrationTime, INT_16U *spectrum);  /* Start acquisition dark spectrum.(Synchronize) */
INT_16S optosky_acquisition_spectrum_sync(INT_32U integrationTime, INT_16U *spectrum);  /* Start acquisition spectrum.(Synchronize) */
INT_8S optosky_acquisition_dark_async(INT_32U integrationTime); /* Start acquisition dark spectrum.(Asynchronous) */
INT_8S optosky_acquisition_spectrum_async(INT_32U integrationTime); /* Start acquisition spectrum.(Asynchronous) */
INT_16S optosky_get_spectrum_data_async(INT_16U *spectrum); /* Get the spectrometer spectrum data.(For asynchronous mode) */

int getActualIntegrationTime(); /* Get the spectrometer integration time. This function declaration is the same as the windows version*/
bool setIntegrationTime(int timeMicros);/* Set the spectrometer integration time. This function declaration is the same as the windows version*/
bool setAverage(int num);/* Set the spectrometer average times. This function declaration is the same as the windows version*/
/////////////////////// Multiple Spectrometers Control Function ///////////////////////
INT_8S optosky_get_specified_dev_integral_time(__Spectrometer_Handle spec_handle, INT_32U *scanTime);
INT_8S optosky_set_specified_dev_integral_time(__Spectrometer_Handle spec_handle, INT_32U scanTime);
INT_8S optosky_set_specified_dev_average(__Spectrometer_Handle spec_handle, INT_16U average);
INT_8S optosky_specified_dev_integral_time_automatic(__Spectrometer_Handle spec_handle, __Integral_Time_Mode mode);/*This feature is only valid with optosky_specified_dev_acquisition_spectrum_sync functions.*/
INT_16S optosky_specified_dev_acquisition_dark_sync(__Spectrometer_Handle spec_handle, INT_32U scanTime, INT_16U *spectrum);
INT_16S optosky_specified_dev_acquisition_spectrum_sync(__Spectrometer_Handle spec_handle, INT_32U scanTime, INT_16U *spectrum);
INT_8S optosky_specified_dev_acquisition_dark_async(__Spectrometer_Handle spec_handle, INT_32U scanTime);
INT_8S optosky_specified_dev_acquisition_spectrum_async(__Spectrometer_Handle spec_handle, INT_32U scanTime);
INT_16S optosky_get_specified_dev_spectrum_data_async(__Spectrometer_Handle spec_handle, INT_16U *spectrum);


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

/////////////////////// Single Spectrometer Control Function ///////////////////////
INT_8S optosky_set_external_GPIO_value(EXT_GPIO_PIN num, EXT_GPIO_VALUE value); /* Set the spectrometer external GPIO value. */
INT_8S optosky_external_trigger_enable(INT_16U integrationTime, void(*external_scan_callback)(INT_16U count, INT_16U *spectrum));   /* Enable the spectrometer external trigger. */
INT_8S optosky_external_trigger_disable(void);  /* Disable the spectrometer external trigger. */

/////////////////////// Multiple Spectrometers Control Function ///////////////////////
INT_8S optosky_set_specified_dev_external_GPIO_value(__Spectrometer_Handle spec_handle, EXT_GPIO_PIN num, EXT_GPIO_VALUE value);
INT_8S optosky_specified_dev_external_trigger_enable(__Spectrometer_Handle spec_handle, \
                                                     INT_16U integrationTime, \
                                                     void(*external_scan_callback)(__Spectrometer_Handle spec_handle,INT_16U count, INT_16U *spectrum));
INT_8S optosky_specified_dev_external_trigger_disable(__Spectrometer_Handle spec_handle);

#ifdef __cplusplus
}
#endif
#endif

