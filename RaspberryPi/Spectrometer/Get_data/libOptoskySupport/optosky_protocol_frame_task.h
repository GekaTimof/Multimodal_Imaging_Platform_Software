#ifndef __OPTOSKY_PROTOCOL
#define __OPTOSKY_PROTOCOL

#include "optosky_support_manager_task.h"
#include "optosky_systemLog_task.h"
#include "libusb.h"
#include <stdio.h>
#include <string.h>
#ifdef __cplusplus
extern "C" {
#endif
#define TRANS_TIMEOUT   1000

#define OPTOSKY_FRAME_HEAD_1    0xAA	/* Header protocol */
#define OPTOSKY_FRAME_HEAD_2    0x55	/* Header protocol */

#define OPTOSKY_FRAME_HEAD_OFF	0		/* protocol HEAD field offset. */
#define OPTOSKY_FRAME_LENGTH_OFF	2	/* protocol length field offset. */
#define OPTOSKY_FRAME_CMD_OFF	4		/* protocol command field offset. */
#define OPTOSKY_FRAME_DATA_OFF	5		/* protocol data field offset. */

/******************* S. OPTOSKY protocol command ID *******************/
#define	OPTOSKY_CMD_GET_VENDOR		0X09
#define OPTOSKY_CMD_GET_PN			0X03
#define OPTOSKY_CMD_GET_SN			0X04
#define OPTOSKY_CMD_GET_VER    		0X02
#define OPTOSKY_CMD_GET_DATE    	0X06
#define OPTOSKY_CMD_GET_BOARD_TEMP	0X01
#define	OPTOSKY_CMD_GET_TEC_TEMP	0X13
#define OPTOSKY_CMD_GET_ATTRIBUTES	0x46

#define OPTOSKY_CMD_GET_SP_COEFFICIENT  0x51
#define OPTOSKY_CMD_GET_NL_COEFFICIENT  0x53
#define OPTOSKY_CMD_GET_WL_COEFFICIENT  0x55
#define OPTOSKY_CMD_GET_DK_COEFFICIENT  0x57

#define	OPTOSKY_CMD_GET_SCAN_TIME	0X41
#define OPTOSKY_CMD_SET_SCAN_TIME	0X14
#define OPTOSKY_CMD_SET_AVERAGE		0X28
#define OPTOSKY_CMD_GET_DARK_SYNC	0X2F
#define OPTOSKY_CMD_GET_SPECTRUM_SYNC	0X1E
#define OPTOSKY_CMD_GET_DARK_ASYNC	0X23
#define OPTOSKY_CMD_GET_SPECTRUM_ASYNC	0X16
#define OPTOSKY_CMD_GET_ASYNC_SPECTRUM_DATA	0x17

#define OPTOSKY_CMD_SET_GPIO_VALUE	0x61
#define OPTOSKY_CMD_ENABLE_EXTTRIG	0x1F
#define OPTOSKY_CMD_GET_SOFT_VER    0xAF  /* get mcu's version */

/******************* E. OPTOSKY protocol command ID *******************/

/******************* OPTOSKY protocol command result *******************/
#define OPTOSKY_CMD_RESULT_SUCCESS	0x00
#define OPTOSKY_CMD_RESULT_FAILURE  0x01

#define OPTOSKY_CMD_ERR_TRANSFER_TIMEOUT    0x01
#define OPTOSKY_CMD_ERR_RECEIVE_TIMEOUT 0x02
#define OPTOSKY_CMD_ERR_CMD_INVALID     0x03
#define OPTOSKY_CMD_ERR_DATA_ERROR      0x04


typedef struct {
    INT_8U paraBuf[1024];
    INT_32U size;
}optosky_cmd_req_msg;

typedef struct {
    INT_8S error;
    INT_16U data_size;
    INT_8U cmd;
    INT_8U dataBuf[10240];
}optosky_cmd_resp_msg;

/******************* excute cmd strcut define *******************/
#define SPEC_INFO_MAX_VENDOR_NAME_LENGTH_CONST	0x0A
#define SPEC_INFO_MAX_PN_NUMBER_LENGTH_CONST	0x0B
#define SPEC_INFO_MAX_SN_NUMBER_LENGTH_CONST	0x10
#define SPEC_INFO_MAX_VERSION_LENGTH_CONST		0x0A
#define SPEC_INFO_MAX_SOFT_VERSION_LENGTH_CONST		0x0A
#define SPEC_INFO_MAX_PRODUCTION_DATE_LENGTH_CONST	0x08
#define SPEC_INFO_MAX_TEMPERATURE_LENGTH_CONST	0x06

typedef struct{
    INT_8U result;
    INT_8U error;
}optosky_resp_v01;

/** @spectrometer_infomation_vendor
    @{
  */
/** Request Message; Registers for get vendor. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_vendor_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_vendor
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U vendor[SPEC_INFO_MAX_VENDOR_NAME_LENGTH_CONST];
    INT_16U vendor_len;
    /**<	 Result code.*/
}optosky_get_vendor_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_pn
    @{
  */
/** Request Message; Registers for get pn. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_pn_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_pn
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U pn[SPEC_INFO_MAX_PN_NUMBER_LENGTH_CONST];
    INT_16U pn_len;
    /**<	 Result code.*/
}optosky_get_pn_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_sn
    @{
  */
/** Request Message; Registers for get sn. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_sn_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_sn
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U sn[SPEC_INFO_MAX_SN_NUMBER_LENGTH_CONST];
    INT_16U sn_len;
    /**<	 Result code.*/
}optosky_get_sn_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_temperature
    @{
  */
/** Request Message; Registers for get temperature. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_temperature_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_temperature
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U temperature[SPEC_INFO_MAX_TEMPERATURE_LENGTH_CONST];
    INT_16U temperature_len;
    /**<	 Result code.*/
}optosky_get_temperature_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_version
    @{
  */
/** Request Message; Registers for get version. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_version_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_version
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U version[SPEC_INFO_MAX_VERSION_LENGTH_CONST];
    INT_16U version_len;
    /**<	 Result code.*/
}optosky_get_version_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_soft_version
    @{
  */
/** Request Message; Registers for get soft_version. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_soft_version_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_soft_version
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U soft_version[SPEC_INFO_MAX_SOFT_VERSION_LENGTH_CONST];
    INT_16U soft_version_len;
    /**<	 Result code.*/
}optosky_get_soft_version_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_production_date
    @{
  */
/** Request Message; Registers for get production date. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_date_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_version
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_8U date[SPEC_INFO_MAX_PRODUCTION_DATE_LENGTH_CONST];
    INT_16U date_len;
    /**<	 Result code.*/
}optosky_get_date_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_infomation_attributes
    @{
  */
/** Request Message; Registers for get attributes. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_attributes_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_infomation_attributes
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    __Spec_attributes attr;
    /**<	 Result code.*/
}optosky_get_attributes_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_dark_coefficient
    @{
  */
/** Request Message; Registers for get dark coefficient. */
typedef struct {
    /* Mandatory */
    INT_16U number_of_coefficients;
    INT_16U send_num;
}optosky_get_dk_coefficient_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_dark_coefficient
	@{
  */
/** Response Message; */
// typedef struct DarkFactor
// {
// 	float k;
// 	float b;
// }s_DARK_FACTOR;

typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_32U pack_count;
    INT_32U iByteSize;
	  INT_32U iFactorLenth;
	  s_DARK_FACTOR DarkFactor[5000];
    /**<	 Result code.*/
}optosky_get_dk_coefficient_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_shape_coefficient
    @{
  */
/** Request Message; Registers for get shape coefficient. */
typedef struct {
    /* Mandatory */
    INT_16U number_of_coefficients;
    INT_16U send_num;
}optosky_get_sp_coefficient_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_shape_coefficient
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_32U pack_count;
    INT_32U iByteSize;
	  INT_32U iFactorLenth;
	  FLOAT ShapeFactor[5000];

    /**<	 Result code.*/
}optosky_get_sp_coefficient_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_nonlinearity_coefficient
    @{
  */
/** Request Message; Registers for get nonlinearity coefficient. */
typedef struct {
    /* Mandatory */
    INT_16U number_of_coefficients;
    INT_16U send_num;
}optosky_get_nl_coefficient_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_nonlinearity_coefficient
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_32U pack_count;
    INT_32U iByteSize;
	  INT_32U iFactorLenth;
    FLOAT LinearFactor[100];
    /**<	 Result code.*/
}optosky_get_nl_coefficient_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_wavelength_coefficient
    @{
  */
/** Request Message; Registers for get wavelength coefficient. */
typedef struct {
    /* Mandatory */
    INT_16U number_of_coefficients;
}optosky_get_wl_coefficient_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_wavelength_coefficient
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    FLOAT coefficient[10];
    /**<	 Result code.*/
}optosky_get_wl_coefficient_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_get_integral_time
    @{
  */
/** Request Message; Registers for get integral time. */
typedef struct {
    /* Mandatory */
    /* This element is a placeholder to prevent the declaration of
     an empty struct.  DO NOT USE THIS FIELD UNDER ANY CIRCUMSTANCE */
    INT_8S __placeholder;
}optosky_get_integral_time_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_get_integral_time
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_32U integral_time;
    /**<	 Result code.*/
}optosky_get_integral_time_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_set_integral_time
    @{
  */
/** Request Message; Registers for set integral time. */
typedef struct {
    /* Mandatory */
    INT_32U integral_time;
}optosky_set_integral_time_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_set_integral_time
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    /**<	 Result code.*/
}optosky_set_integral_time_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_set_average
    @{
  */
/** Request Message; Registers for set average. */
typedef struct {
    /* Mandatory */
    INT_16U average;
}optosky_set_average_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_set_average
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    /**<	 Result code.*/
}optosky_set_average_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_spectrum_control
    @{
  */
/** Request Message; Registers for set average. */
typedef struct {
    /* Mandatory */
    INT_32U integral_time;
}optosky_spectrum_control_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_spectrum_control
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    INT_16U *spectrum;
    INT_16U pixel_length;
    /**<	 Result code.*/
}optosky_spectrum_control_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_outside_gpio_control
    @{
  */
/** Request Message; Registers for set outside gpio control. */
typedef struct {
    /* Mandatory */
    INT_16U control_flag;
}optosky_set_outside_gpio_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_outside_gpio_control
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    /**<	 Result code.*/
}optosky_set_outside_gpio_resp_msg;  /* Message */
/**
	@}
  */

/** @spectrometer_outside_trigger_scan
    @{
  */
/** Request Message; Registers for set outside trigger scan. */
typedef struct {
    /* Mandatory */
    INT_16U integral_time;
}optosky_outside_trigger_req_msg;  /* Message */
/**
    @}
  */

/** @spectrometer_outside_trigger_scan
	@{
  */
/** Response Message; */
typedef struct {
    /* Mandatory */
    /*  Result Code */
    optosky_resp_v01 resp;
    /**<	 Result code.*/
}optosky_outside_trigger_resp_msg;  /* Message */
/**
	@}
  */




/****************** END ******************/
void Optosky_excute_command_sync(__Optosky_Spec *optoskySpec,
								 INT_8U CMD_ID,
								 void *req_msg,
								 void *resp_msg);

#ifdef __cplusplus
}
#endif

#endif
