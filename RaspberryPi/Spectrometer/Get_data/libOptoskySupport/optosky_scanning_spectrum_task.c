#include "optosky_support_manager_task.h"
#include "optosky_protocol_frame_task.h"
#include "optosky_systemLog_task.h"

#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <stdlib.h>
#include <stdbool.h>

#define Automatic_target_value  50000   /* the target value of the automatic integration time function. */

#define SCAN_SPEC_LOG(fmt, ...)	OPTOSKY_LOG_MSG_FILE("SCAN", fmt, ##__VA_ARGS__)

extern libusb_device_handle *usb_handle;
extern char optosky_interface_manager_state;
extern __Optosky_Spec optoskySpec;

////////////////////////////////////private/////////////////////////////////////////////////
INT_16U acquisition_spectrum_response_maxnum(__Optosky_Spec *optoskyCtrl, INT_32U integration_time, INT_16U *spectrum, INT_16U *pixel_length)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec.specInfo.attributes.pixel_number };

	spectrum_resp_msg.spectrum = malloc(optoskySpec.specInfo.attributes.pixel_number << 1);
	if (spectrum_resp_msg.spectrum == NULL) {
		return 0;
	}
	spectrum_req_msg.integral_time = integration_time;
	Optosky_excute_command_sync(optoskyCtrl,
		OPTOSKY_CMD_GET_SPECTRUM_SYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {

		if (spectrum_resp_msg.pixel_length != optoskySpec.specInfo.attributes.pixel_number)
		{
			SCAN_SPEC_LOG("[%s] Command return error pixel length not equal!\n", __FUNCTION__);
			free(spectrum_resp_msg.spectrum);
			return 0;
		}

		INT_16U index, index_max = 0;
		memcpy(spectrum, spectrum_resp_msg.spectrum, (spectrum_resp_msg.pixel_length << 1));
		*pixel_length = spectrum_resp_msg.pixel_length;
		for (index = 0; index < optoskySpec.specInfo.attributes.pixel_number; index++) {
			if (spectrum[index] > spectrum[index_max]) {
				index_max = index;
			}
		}

		free(spectrum_resp_msg.spectrum);
		return spectrum[index_max];
	}
	else {
		free(spectrum_resp_msg.spectrum);
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
		return 0;
	}
}

/////////////////////////////////////////////////////////////////////////////////////////////
INT_8S optosky_get_integral_time(INT_32U *scanTime)
{
	optosky_get_integral_time_req_msg get_integral_time_req_msg;
	optosky_get_integral_time_resp_msg get_integral_time_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&get_integral_time_req_msg, 0x00, sizeof(get_integral_time_req_msg));
	memset(&get_integral_time_resp_msg, 0x00, sizeof(get_integral_time_resp_msg));

	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_GET_SCAN_TIME,
		&get_integral_time_req_msg,
		&get_integral_time_resp_msg);
	if (get_integral_time_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		*scanTime = get_integral_time_resp_msg.integral_time;
		if (optoskySpec.specInfo.attributes.integral_unit == IntegralTime_Unit_ms) {
			SCAN_SPEC_LOG("Current integral time is %dms\n", *scanTime);
		}
		else {
			SCAN_SPEC_LOG("Current integral time is %dus\n", *scanTime);
		}
		return 0;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, get_integral_time_resp_msg.resp.error);
		return get_integral_time_resp_msg.resp.error;
	}
}

/*----------------------------------------------------------------------------*/
int getActualIntegrationTime()
{
	int scanTime;
	optosky_get_integral_time_req_msg get_integral_time_req_msg;
	optosky_get_integral_time_resp_msg get_integral_time_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&get_integral_time_req_msg, 0x00, sizeof(get_integral_time_req_msg));
	memset(&get_integral_time_resp_msg, 0x00, sizeof(get_integral_time_resp_msg));

	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_GET_SCAN_TIME,
		&get_integral_time_req_msg,
		&get_integral_time_resp_msg);
	if (get_integral_time_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		scanTime = get_integral_time_resp_msg.integral_time;
		if (optoskySpec.specInfo.attributes.integral_unit == IntegralTime_Unit_ms) {
			SCAN_SPEC_LOG("Current integral time is %dms\n", scanTime);
		}
		else {
			SCAN_SPEC_LOG("Current integral time is %dus\n", scanTime);
		}
		return scanTime;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, get_integral_time_resp_msg.resp.error);
		//return get_integral_time_resp_msg.resp.error;
		return 0;
	}
}



bool setIntegrationTime(int timeMicros)
{
	optosky_set_integral_time_req_msg set_integral_time_req_msg;
	optosky_set_integral_time_resp_msg set_integral_time_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&set_integral_time_req_msg, 0x00, sizeof(set_integral_time_req_msg));
	memset(&set_integral_time_resp_msg, 0x00, sizeof(set_integral_time_resp_msg));

	set_integral_time_req_msg.integral_time = timeMicros;
	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_SET_SCAN_TIME,
		&set_integral_time_req_msg,
		&set_integral_time_resp_msg);
	if (set_integral_time_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		return true;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, set_integral_time_resp_msg.resp.error);
		return false;//return set_integral_time_resp_msg.resp.error;
	}
}
/*----------------------------------------------------------------------------*/

INT_8S optosky_set_integral_time(INT_32U scanTime)
{
	optosky_set_integral_time_req_msg set_integral_time_req_msg;
	optosky_set_integral_time_resp_msg set_integral_time_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&set_integral_time_req_msg, 0x00, sizeof(set_integral_time_req_msg));
	memset(&set_integral_time_resp_msg, 0x00, sizeof(set_integral_time_resp_msg));

	set_integral_time_req_msg.integral_time = scanTime;
	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_SET_SCAN_TIME,
		&set_integral_time_req_msg,
		&set_integral_time_resp_msg);
	if (set_integral_time_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		return 0;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, set_integral_time_resp_msg.resp.error);
		return set_integral_time_resp_msg.resp.error;
	}
}

INT_8S optosky_set_average(INT_16U average)
{
	optosky_set_average_req_msg	set_average_req_msg;
	optosky_set_average_resp_msg set_average_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&set_average_req_msg, 0x00, sizeof(set_average_req_msg));
	memset(&set_average_resp_msg, 0x00, sizeof(set_average_resp_msg));

	set_average_req_msg.average = average;
	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_SET_AVERAGE,
		&set_average_req_msg,
		&set_average_resp_msg);
	if (set_average_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		return 0;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, set_average_resp_msg.resp.error);
		return set_average_resp_msg.resp.error;
	}
}

/*----------------------------------------------------------------------*/
bool setAverage(int num)
{
	optosky_set_average_req_msg	set_average_req_msg;
	optosky_set_average_resp_msg set_average_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return false;
	}

	memset(&set_average_req_msg, 0x00, sizeof(set_average_req_msg));
	memset(&set_average_resp_msg, 0x00, sizeof(set_average_resp_msg));

	set_average_req_msg.average = num;
	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_SET_AVERAGE,
		&set_average_req_msg,
		&set_average_resp_msg);
	if (set_average_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		return true;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, set_average_resp_msg.resp.error);
		return false;//return set_average_resp_msg.resp.error;
	}
}
/*----------------------------------------------------------------------*/


INT_8S optosky_integral_time_automatic(__Integral_Time_Mode mode)
{
	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	if (mode == IntegralTime_Automatic_Enable) {
		optoskySpec.integralMode = IntegralTime_Automatic_Enable;
	}
	else if (mode == IntegralTime_Automatic_Disable) {
		optoskySpec.integralMode = IntegralTime_Automatic_Disable;
	}
	else {
		/* invalid parameter... */
		return (-1);
	}
	return 0;
}

INT_16S optosky_acquisition_dark_sync(INT_32U scanTime, INT_16U *spectrum)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec.specInfo.attributes.pixel_number };

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	spectrum_resp_msg.spectrum = malloc((optoskySpec.specInfo.attributes.pixel_number << 1));
	if (spectrum_resp_msg.spectrum == NULL) {
		return (-1);
	}

	spectrum_req_msg.integral_time = scanTime;
	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_GET_DARK_SYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(spectrum, spectrum_resp_msg.spectrum, (spectrum_resp_msg.pixel_length << 1));
		free(spectrum_resp_msg.spectrum);
		return spectrum_resp_msg.pixel_length;
	}
	else {
		free(spectrum_resp_msg.spectrum);
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
		return 0;
	}
}

INT_16S optosky_acquisition_spectrum_sync(INT_32U scanTime, INT_16U *spectrum)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec.specInfo.attributes.pixel_number };

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	if (optoskySpec.integralMode == IntegralTime_Automatic_Disable) {    /* Custom integration time. */
		spectrum_resp_msg.spectrum = malloc(optoskySpec.specInfo.attributes.pixel_number << 1);
		if (spectrum_resp_msg.spectrum == NULL) {
			return (-1);
		}
		spectrum_req_msg.integral_time = scanTime;
		Optosky_excute_command_sync(&optoskySpec,
			OPTOSKY_CMD_GET_SPECTRUM_SYNC,
			&spectrum_req_msg,
			&spectrum_resp_msg);
		if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
			memcpy(spectrum, spectrum_resp_msg.spectrum, spectrum_resp_msg.pixel_length << 1);
			free(spectrum_resp_msg.spectrum);
			return spectrum_resp_msg.pixel_length;
		}
		else {
			free(spectrum_resp_msg.spectrum);
			SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
			return 0;
		}
	}
	else {     /* Automatic integration time. */
	   /* 1. Get base spectrum */
		INT_16U ret = 0;
		INT_32U integral_time = 0;
		INT_32U max_time = 0;
		INT_16U pixel_length = optoskySpec.specInfo.attributes.pixel_number;
		float multiple = 1;
		INT_16U *spectrum_tmp = malloc((optoskySpec.specInfo.attributes.pixel_number << 1));

		integral_time = optoskySpec.specInfo.attributes.integral_unit == IntegralTime_Unit_ms ? \
			1 : 1000;
		max_time = optoskySpec.specInfo.attributes.integral_size == IntegralTime_Size_16 ? \
			0xFFFF : 0xFFFFFFFF;

		do {
			integral_time *= multiple;
			if (integral_time >= max_time) {
				break;
			}
			ret = acquisition_spectrum_response_maxnum(&optoskySpec, integral_time, spectrum_tmp, &pixel_length);
			if (ret != 0) {
				multiple = (float)Automatic_target_value / ret;
			}
			else {
				free(spectrum_tmp);
				return 0;
			}
		} while (multiple > 1);

		SCAN_SPEC_LOG("Info automatic integration time pixel length 0 (%d)!\n", pixel_length);
		SCAN_SPEC_LOG("Info automatic integration time pixel length 1 (%d)!\n", optoskySpec.specInfo.attributes.pixel_number);

		memcpy(spectrum, spectrum_tmp, (pixel_length << 1));
		free(spectrum_tmp);

		return pixel_length;
	}
}

INT_8S optosky_acquisition_dark_async(INT_32U scanTime)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&spectrum_req_msg, 0x00, sizeof(spectrum_req_msg));
	memset(&spectrum_resp_msg, 0x00, sizeof(spectrum_resp_msg));

	spectrum_req_msg.integral_time = scanTime;

	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_GET_DARK_ASYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	return spectrum_resp_msg.resp.result;
}

INT_8S optosky_acquisition_spectrum_async(INT_32U scanTime)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg;

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	memset(&spectrum_req_msg, 0x00, sizeof(spectrum_req_msg));
	memset(&spectrum_resp_msg, 0x00, sizeof(spectrum_resp_msg));

	spectrum_req_msg.integral_time = scanTime;

	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_GET_SPECTRUM_ASYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	return spectrum_resp_msg.resp.result;
}

INT_16S optosky_get_spectrum_data_async(INT_16U *spectrum)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec.specInfo.attributes.pixel_number };

	if (!optosky_interface_manager_state) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	spectrum_resp_msg.spectrum = malloc(optoskySpec.specInfo.attributes.pixel_number << 1);
	if (spectrum_resp_msg.spectrum == NULL) {
		return (-1);
	}

	Optosky_excute_command_sync(&optoskySpec,
		OPTOSKY_CMD_GET_ASYNC_SPECTRUM_DATA,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(spectrum, spectrum_resp_msg.spectrum, (spectrum_resp_msg.pixel_length << 1));
		free(spectrum_resp_msg.spectrum);
		return spectrum_resp_msg.pixel_length;
	}
	else {
		free(spectrum_resp_msg.spectrum);
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
		return 0;
	}
}

INT_8S optosky_spectrum_data_handler(void)
{
	/* FixMe. spectrum data handler */
}
#include<time.h>
#include<sys/time.h>
#include "libusb.h"

int optosky_speed_test_handler(INT_32U scanTime)
{
	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec.specInfo.attributes.pixel_number };

	struct timeval starttime, endtime;
	double timeuse;
	int fps = 0;

	spectrum_resp_msg.spectrum = malloc(optoskySpec.specInfo.attributes.pixel_number << 1);
	if (spectrum_resp_msg.spectrum == NULL) {
		return (-1);
	}
	spectrum_req_msg.integral_time = scanTime;
	gettimeofday(&starttime, NULL);
	/*
	do{
		Optosky_excute_command_sync(&optoskySpec,
									OPTOSKY_CMD_GET_SPECTRUM_SYNC,
									&spectrum_req_msg,
									&spectrum_resp_msg);
		 if(spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
			 gettimeofday(&endtime, NULL);
			 timeuse = 1000000*(endtime.tv_sec - starttime.tv_sec) + endtime.tv_usec - starttime.tv_usec;
		 }else {
			SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
			return 0;
		}
		fps++;
	}while(timeuse <= 1000000);
	*/
	/*
		while(1) {
			Optosky_excute_command_sync(&optoskySpec,
										OPTOSKY_CMD_GET_SPECTRUM_SYNC,
										&spectrum_req_msg,
										&spectrum_resp_msg);
			 if(spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
				 gettimeofday(&endtime, NULL);
				 timeuse = 1000000 * (endtime.tv_sec - starttime.tv_sec) + endtime.tv_usec - starttime.tv_usec;
			 }else {
				SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
				return 0;
			}
			fps++;
			if(timeuse >= 1000000) {
				break;
			}
		}
	*/
	INT_8S ret = 0;
	INT_16U index = 0;
	INT_16U tmpBuf_len = 0;
	INT_8U data_length;
	INT_32U length = 0;
	INT_8U tmpBuf_R[6000] = { 0 };
	INT_8U tmpBuf[28] = { OPTOSKY_FRAME_HEAD_1, OPTOSKY_FRAME_HEAD_2, 0x00, 0x08 };

	tmpBuf[OPTOSKY_FRAME_CMD_OFF] = 0x1E;
	tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (scanTime >> 24);
	tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (scanTime >> 16);
	tmpBuf[OPTOSKY_FRAME_DATA_OFF + 2] = (scanTime >> 8);
	tmpBuf[OPTOSKY_FRAME_DATA_OFF + 3] = scanTime & 0xFF;
	data_length = 7;
	tmpBuf[data_length + 2] = 0;
	for (index = 0; index < data_length; index++) {
		tmpBuf[data_length + 2] += tmpBuf[index + 2];
	}
	tmpBuf_len = data_length + 3;

	do {
		ret = libusb_bulk_transfer(optoskySpec.usbHandler, BULK_ENDPOINT_OUT, tmpBuf, tmpBuf_len, &length, 10000);
		if (ret != 0) {
			free(spectrum_resp_msg.spectrum);
			return 0;
		}
		ret = libusb_bulk_transfer(optoskySpec.usbHandler, BULK_ENDPOINT_IN, tmpBuf_R, 5000, &length, (TRANS_TIMEOUT + scanTime));
		if (ret != 0) {
			free(spectrum_resp_msg.spectrum);
			return 0;
		}
		gettimeofday(&endtime, NULL);
		fps++;
	} while (timeuse <= 1000000);

	free(spectrum_resp_msg.spectrum);
	return fps;
}

////////////////////// Multiple Spectrometer Device Function //////////////////////
INT_8S optosky_get_specified_dev_integral_time(__Spectrometer_Handle spec_handle, INT_32U *scanTime)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_get_integral_time_req_msg get_integral_time_req_msg;
	optosky_get_integral_time_resp_msg get_integral_time_resp_msg;

	memset(&get_integral_time_req_msg, 0x00, sizeof(get_integral_time_req_msg));
	memset(&get_integral_time_resp_msg, 0x00, sizeof(get_integral_time_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_GET_SCAN_TIME,
		&get_integral_time_req_msg,
		&get_integral_time_resp_msg);
	if (get_integral_time_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		*scanTime = get_integral_time_resp_msg.integral_time;
		if (optoskySpec->specInfo.attributes.integral_unit == IntegralTime_Unit_ms) {
			SCAN_SPEC_LOG("Current integral time is %dms\n", *scanTime);
		}
		else {
			SCAN_SPEC_LOG("Current integral time is %dus\n", *scanTime);
		}
		return 0;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, get_integral_time_resp_msg.resp.error);
		return get_integral_time_resp_msg.resp.error;
	}
}

INT_8S optosky_set_specified_dev_integral_time(__Spectrometer_Handle spec_handle, INT_32U scanTime)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_set_integral_time_req_msg set_integral_time_req_msg;
	optosky_set_integral_time_resp_msg set_integral_time_resp_msg;

	memset(&set_integral_time_req_msg, 0x00, sizeof(set_integral_time_req_msg));
	memset(&set_integral_time_resp_msg, 0x00, sizeof(set_integral_time_resp_msg));

	set_integral_time_req_msg.integral_time = scanTime;
	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_SET_SCAN_TIME,
		&set_integral_time_req_msg,
		&set_integral_time_resp_msg);
	if (set_integral_time_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		return 0;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, set_integral_time_resp_msg.resp.error);
		return set_integral_time_resp_msg.resp.error;
	}
}

INT_8S optosky_set_specified_dev_average(__Spectrometer_Handle spec_handle, INT_16U average)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_set_average_req_msg	set_average_req_msg;
	optosky_set_average_resp_msg set_average_resp_msg;

	memset(&set_average_req_msg, 0x00, sizeof(set_average_req_msg));
	memset(&set_average_resp_msg, 0x00, sizeof(set_average_resp_msg));

	set_average_req_msg.average = average;
	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_SET_AVERAGE,
		&set_average_req_msg,
		&set_average_resp_msg);
	if (set_average_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		return 0;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, set_average_resp_msg.resp.error);
		return set_average_resp_msg.resp.error;
	}
}

INT_8S optosky_specified_dev_integral_time_automatic(__Spectrometer_Handle spec_handle, __Integral_Time_Mode mode)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	if (mode == IntegralTime_Automatic_Enable) {
		optoskySpec->integralMode = IntegralTime_Automatic_Enable;
	}
	else if (mode == IntegralTime_Automatic_Disable) {
		optoskySpec->integralMode = IntegralTime_Automatic_Disable;
	}
	else {
		/* invalid parameter... */
		return (-1);
	}
	return 0;
}

INT_16S optosky_specified_dev_acquisition_dark_sync(__Spectrometer_Handle spec_handle, INT_32U scanTime, INT_16U *spectrum)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec->specInfo.attributes.pixel_number };

	spectrum_resp_msg.spectrum = malloc(optoskySpec->specInfo.attributes.pixel_number << 1);
	if (spectrum_resp_msg.spectrum == NULL) {
		return (-1);
	}

	spectrum_req_msg.integral_time = scanTime;
	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_GET_DARK_SYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(spectrum, spectrum_resp_msg.spectrum, (spectrum_resp_msg.pixel_length << 1));
		free(spectrum_resp_msg.spectrum);
		return spectrum_resp_msg.pixel_length;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
		free(spectrum_resp_msg.spectrum);
		return 0;
	}
}

INT_16S optosky_specified_dev_acquisition_spectrum_sync(__Spectrometer_Handle spec_handle, INT_32U scanTime, INT_16U *spectrum)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	if (optoskySpec->integralMode == IntegralTime_Automatic_Disable) {    /* Custom integration time. */
		optosky_spectrum_control_req_msg spectrum_req_msg;
		optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec->specInfo.attributes.pixel_number };

		spectrum_resp_msg.spectrum = malloc((optoskySpec->specInfo.attributes.pixel_number << 1));
		if (spectrum_resp_msg.spectrum == NULL) {
			return (-1);
		}

		spectrum_req_msg.integral_time = scanTime;
		Optosky_excute_command_sync(optoskySpec,
			OPTOSKY_CMD_GET_SPECTRUM_SYNC,
			&spectrum_req_msg,
			&spectrum_resp_msg);
		if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
			memcpy(spectrum, spectrum_resp_msg.spectrum, (spectrum_resp_msg.pixel_length << 1));
			free(spectrum_resp_msg.spectrum);
			return spectrum_resp_msg.pixel_length;
		}
		else {
			SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
			free(spectrum_resp_msg.spectrum);
			return 0;
		}
	}
	else {
		/* Automatic integration time. */
		INT_16U ret = 0;
		INT_32U integral_time = 0;
		INT_32U max_time = 0;
		INT_16U pixel_length = 0;
		float multiple = 1;

		printf("pixel size : %d\n", optoskySpec->specInfo.attributes.pixel_number);
		INT_16U *spectrum_tmp = malloc((optoskySpec->specInfo.attributes.pixel_number << 1));

		if (spectrum_tmp == NULL) {
			printf("malloc error!\n");
			return -1;
		}
		integral_time = optoskySpec->specInfo.attributes.integral_unit == IntegralTime_Unit_ms ? \
			10 : 10000;
		max_time = optoskySpec->specInfo.attributes.integral_size == IntegralTime_Size_16 ? \
			0xFFFF : 0xFFFFFFFF;
		do {
			integral_time *= multiple;
			if (integral_time >= max_time) {
				break;
			}
			ret = acquisition_spectrum_response_maxnum(optoskySpec, integral_time, spectrum_tmp, &pixel_length);
			if (ret != 0) {
				multiple = (float)Automatic_target_value / ret;
				usleep(5000);
			}
			else {
				free(spectrum_tmp);
				return 0;
			}
		} while (multiple > 1);
		memcpy(spectrum, spectrum_tmp, (pixel_length << 1));
		free(spectrum_tmp);
		return pixel_length;
	}
}

INT_8S optosky_specified_dev_acquisition_dark_async(__Spectrometer_Handle spec_handle, INT_32U scanTime)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg;

	memset(&spectrum_req_msg, 0x00, sizeof(spectrum_req_msg));
	memset(&spectrum_resp_msg, 0x00, sizeof(spectrum_resp_msg));
	spectrum_req_msg.integral_time = scanTime;

	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_GET_DARK_ASYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	return spectrum_resp_msg.resp.result;
}

INT_8S optosky_specified_dev_acquisition_spectrum_async(__Spectrometer_Handle spec_handle, INT_32U scanTime)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg;

	memset(&spectrum_req_msg, 0x00, sizeof(spectrum_req_msg));
	memset(&spectrum_resp_msg, 0x00, sizeof(spectrum_resp_msg));

	spectrum_req_msg.integral_time = scanTime;

	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_GET_SPECTRUM_ASYNC,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	return spectrum_resp_msg.resp.result;
}

INT_16S optosky_get_specified_dev_spectrum_data_async(__Spectrometer_Handle spec_handle, INT_16U *spectrum)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-6);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL || optoskySpec->isOpen == 0) {
		SCAN_SPEC_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
		return (-10);
	}

	optosky_spectrum_control_req_msg spectrum_req_msg;
	optosky_spectrum_control_resp_msg spectrum_resp_msg = { .pixel_length = optoskySpec->specInfo.attributes.pixel_number };

	spectrum_resp_msg.spectrum = malloc(optoskySpec->specInfo.attributes.pixel_number << 1);
	if (spectrum_resp_msg.spectrum == NULL) {
		return (-1);
	}

	Optosky_excute_command_sync(optoskySpec,
		OPTOSKY_CMD_GET_ASYNC_SPECTRUM_DATA,
		&spectrum_req_msg,
		&spectrum_resp_msg);
	if (spectrum_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(spectrum, spectrum_resp_msg.spectrum, (spectrum_resp_msg.pixel_length << 1));
		free(spectrum_resp_msg.spectrum);
		return spectrum_resp_msg.pixel_length;
	}
	else {
		SCAN_SPEC_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, spectrum_resp_msg.resp.error);
		free(spectrum_resp_msg.spectrum);
		return 0;
	}
}



