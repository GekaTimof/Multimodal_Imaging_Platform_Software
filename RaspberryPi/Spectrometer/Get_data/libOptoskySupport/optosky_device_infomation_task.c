#include "optosky_support_manager_task.h"
#include "optosky_protocol_frame_task.h"
#include <stdio.h>
#include <string.h>

#define MODULE_INFO_LOG(fmt, ...)  OPTOSKY_LOG_MSG_FILE("INFO", fmt, ##__VA_ARGS__)
extern libusb_device_handle *usb_handle;
extern char optosky_interface_manager_state;
extern __Optosky_Spec optoskySpec;

INT_8S optosky_get_vendor(INT_8S* vendor, INT_8U vendor_size)
{
	optosky_get_vendor_req_msg	vendor_req_msg;
	optosky_get_vendor_resp_msg vendor_resp_msg;

    if(!optosky_interface_manager_state) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
	memset(&vendor_req_msg, 0x00, sizeof(vendor_req_msg));
	memset(&vendor_resp_msg, 0x00, sizeof(vendor_resp_msg));
    
	Optosky_excute_command_sync(&optoskySpec, 
								OPTOSKY_CMD_GET_VENDOR,
								&vendor_req_msg,
								&vendor_resp_msg);
	if(vendor_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(vendor, vendor_resp_msg.vendor , \
		   	       (vendor_resp_msg.vendor_len > vendor_size) ? vendor_size : vendor_resp_msg.vendor_len);
		return vendor_resp_msg.vendor_len;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, vendor_resp_msg.resp.error);
		return vendor_resp_msg.resp.error;
	}
}

INT_8S optosky_get_PN(INT_8S* pn, INT_8U pn_size)
{
	optosky_get_pn_req_msg	pn_req_msg;
	optosky_get_pn_resp_msg pn_resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&pn_req_msg, 0x00, sizeof(pn_req_msg));
	memset(&pn_resp_msg, 0x00, sizeof(pn_resp_msg));

	Optosky_excute_command_sync(&optoskySpec,
								OPTOSKY_CMD_GET_PN,
								&pn_req_msg,
								&pn_resp_msg);
	if(pn_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(pn, pn_resp_msg.pn, \
		   	       (pn_resp_msg.pn_len > pn_size) ? pn_size : pn_resp_msg.pn_len);
		return pn_resp_msg.pn_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, pn_resp_msg.resp.error);
		return pn_resp_msg.resp.error;
	}
}

INT_8S optosky_get_SN(INT_8S* sn, INT_8U sn_size)
{
	optosky_get_sn_req_msg	sn_req_msg;
	optosky_get_sn_resp_msg sn_resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&sn_req_msg, 0x00, sizeof(sn_req_msg));
	memset(&sn_resp_msg, 0x00, sizeof(sn_resp_msg));

	Optosky_excute_command_sync(&optoskySpec, 
								OPTOSKY_CMD_GET_SN,
								&sn_req_msg,
								&sn_resp_msg);
	if(sn_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(sn, sn_resp_msg.sn , \
		   	       (sn_resp_msg.sn_len > sn_size) ? sn_size : sn_resp_msg.sn_len);
		return sn_resp_msg.sn_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, sn_resp_msg.resp.error);
		return sn_resp_msg.resp.error;
	}

}

INT_8S optosky_get_version(INT_8S* version, INT_8U version_size)
{
	optosky_get_version_req_msg	version_req_msg;
	optosky_get_version_resp_msg version_resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&version_req_msg, 0x00, sizeof(version_req_msg));
	memset(&version_resp_msg, 0x00, sizeof(version_resp_msg));

	Optosky_excute_command_sync(&optoskySpec, 
								OPTOSKY_CMD_GET_VER,
								&version_req_msg,
								&version_resp_msg);
	if(version_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(version, version_resp_msg.version , \
		   	       (version_resp_msg.version_len > version_size) ? version_size : version_resp_msg.version_len);
		return version_resp_msg.version_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, version_resp_msg.resp.error);
		return version_resp_msg.resp.error;
	}
}

INT_8S optosky_get_soft_version(INT_8S* version, INT_8U version_size)
{
	optosky_get_soft_version_req_msg	version_req_msg;
	optosky_get_soft_version_resp_msg version_resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&version_req_msg, 0x00, sizeof(version_req_msg));
	memset(&version_resp_msg, 0x00, sizeof(version_resp_msg));

	Optosky_excute_command_sync(&optoskySpec, 
								OPTOSKY_CMD_GET_SOFT_VER,
								&version_req_msg,
								&version_resp_msg);
	if(version_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(version, version_resp_msg.soft_version , \
		   	       (version_resp_msg.soft_version_len > version_size) ? version_size : version_resp_msg.soft_version_len);
		return version_resp_msg.soft_version_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, version_resp_msg.resp.error);
		return version_resp_msg.resp.error;
	}
}

INT_8S optosky_get_production_date(INT_8S* date, INT_8U date_size)
{
	optosky_get_date_req_msg date_req_msg;
	optosky_get_date_resp_msg date_resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&date_req_msg, 0x00, sizeof(date_req_msg));
	memset(&date_resp_msg, 0x00, sizeof(date_resp_msg));

	Optosky_excute_command_sync(&optoskySpec, 
								OPTOSKY_CMD_GET_DATE,
								&date_req_msg,
								&date_resp_msg);
	if(date_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(date, date_resp_msg.date , \
		   	       (date_resp_msg.date_len > date_size) ? date_size : date_resp_msg.date_len);
		return date_resp_msg.date_len;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, date_resp_msg.resp.error);
		return date_resp_msg.resp.error;
	}
}

INT_8S optosky_get_TEC_temperature(INT_8S* temperature, INT_8U temperature_size)
{
	optosky_get_temperature_req_msg	temperature_req_msg;
	optosky_get_temperature_resp_msg temperature_resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&temperature_req_msg, 0x00, sizeof(temperature_req_msg));
	memset(&temperature_resp_msg, 0x00, sizeof(temperature_resp_msg));

	Optosky_excute_command_sync(&optoskySpec,
								OPTOSKY_CMD_GET_TEC_TEMP,
								&temperature_req_msg,
								&temperature_resp_msg);
	if(temperature_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(temperature, temperature_resp_msg.temperature, \
               (temperature_resp_msg.temperature_len > temperature_size) ? temperature_size : temperature_resp_msg.temperature_len);
		return temperature_resp_msg.temperature_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, temperature_resp_msg.resp.error);
		return temperature_resp_msg.resp.error;
	}
}

INT_8S optosky_get_attributes(__Spec_attributes *attributes)
{
	optosky_get_attributes_req_msg attr_req_msg;
	optosky_get_attributes_resp_msg attr_resp_msg;

	if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&attr_req_msg, 0x00, sizeof(attr_req_msg));
	memset(&attr_resp_msg, 0x00, sizeof(attr_resp_msg));

	Optosky_excute_command_sync(&optoskySpec,
								OPTOSKY_CMD_GET_ATTRIBUTES,
								&attr_req_msg,
								&attr_resp_msg);
	if(attr_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		*attributes = attr_resp_msg.attr;
		return 0;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, attr_resp_msg.resp.error);
		return attr_resp_msg.resp.error;
	}
}

__Attr_Integral_Length optosky_get_integral_time_length(void)
{
    return optoskySpec.specInfo.attributes.integral_size;
}

__Attr_Integral_Unit optosky_get_integral_time_unit(void)
{
    return optoskySpec.specInfo.attributes.integral_unit;
}

INT_16U optosky_get_pixel_length(void)
{
    return optoskySpec.specInfo.attributes.pixel_number;
}


/*****************************************************************************************
* param:
*	start: start index of str1
* return:
* -1: the first character that does not match has a lower value in str1 than in str2
*  1: the first character that does not match has a greater value in str1 than in str2
*  0: the contents of both strings are equal
******************************************************************************************/
int _comparePartStr(const unsigned char* str1, const char* str2, int start, int len) {
	int res = 0;

	for (int i = 0; i < len; i++) {
		if (str1[start + i] < str2[i])
		{
			res = -1;
			break;
		}
		else if (str1[start + i] > str2[i]) {
			res = 1;
			break;
		}
	}

	return res;
}



int _getPixelCount(const unsigned char* m_pn) {

	int res = 2048;

	if (0 == _comparePartStr(m_pn, "1", 3, 1)) {
		res = 1024;

		if (0 == _comparePartStr(m_pn, "1010", 3, 4))
			res = 512;
	}
	else if (0 == _comparePartStr(m_pn, "2", 3, 1)) {
		if (0 == _comparePartStr(m_pn, "2100", 3, 4))
			res = 512;
	}
	else if (0 == _comparePartStr(m_pn, "3", 3, 1)) {
		res = 4096;

		if (0 == _comparePartStr(m_pn, "3030", 3, 4) || 0 == _comparePartStr(m_pn, "3330", 3, 4))
			res = 2048;
	}
	else if (0 == _comparePartStr(m_pn, "4", 3, 1)) {
		res = 3648;
	}
	else if (0 == _comparePartStr(m_pn, "5", 3, 1)) {
		if (0 == _comparePartStr(m_pn, "5334", 3, 4) || 0 == _comparePartStr(m_pn, "5034", 3, 4) || 0 == _comparePartStr(m_pn, "5040", 3, 4))
			res = 4096;

		// TODO: 5100 support
	}
	else if (0 == _comparePartStr(m_pn, "6", 3, 1)) {
		res = 1024;
	}
	else if (0 == _comparePartStr(m_pn, "8", 3, 1)) {
		res = 512;
		if (0 == _comparePartStr(m_pn, "8600", 3, 4))
			res = 256;
	}
	else if (0 == _comparePartStr(m_pn, "9", 3, 1)) {

		if (0 == _comparePartStr(m_pn, "9100d", 3, 5) || 0 == _comparePartStr(m_pn, "9100D", 3, 5))
			res = 512;
	}

	return res;
}

int getPixelCount()
{
	int m_pixelCount;

    INT_8S pn_info[11] = {0};
	unsigned char pn[11] = {0};

    INT_8S ret = optosky_get_PN(pn_info, 11);
    if(ret < 0) {
		return (-1);
    }else {
        INT_8S index = 0;       

        for (index = 0; index < ret; index++)
        {
			pn[index] = (unsigned char)pn_info[index];
        }
    }
	m_pixelCount = _getPixelCount(pn);
	return m_pixelCount;
}

#if 0
INT_8S optosky_get_board_temp(INT_8S* temp, INT_8U temp_size)
{
	optosky_cmd_req_msg	req_msg;
	optosky_cmd_resp_msg resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&req_msg, 0x00, sizeof(req_msg));
	memset(&resp_msg, 0x00, sizeof(resp_msg));

	Optosky_excute_command_sync(usb_handler, 
								OPTOSKY_CMD_GET_BOARD_TEMP,
								&req_msg,
								&resp_msg);
	if(resp_msg.error == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(temp, resp_msg.dataBuf , \
		  	 	       (resp_msg.data_size > temp_size) ? temp_size : resp_msg.data_size);
		return resp_msg.data_size;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, resp_msg.error);
		return resp_msg.error;
	}
}

INT_8S optosky_get_tec_temp(INT_8S* temp, INT_8U temp_size)
{
	optosky_cmd_req_msg	req_msg;
	optosky_cmd_resp_msg resp_msg;

    if(!optosky_interface_manager_state) {
		MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&req_msg, 0x00, sizeof(req_msg));
	memset(&resp_msg, 0x00, sizeof(resp_msg));

	Optosky_excute_command_sync(usb_handler, 
								OPTOSKY_CMD_GET_TEC_TEMP,
								&req_msg,
								&resp_msg);
	if(resp_msg.error == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(temp, resp_msg.dataBuf , \
		     	  (resp_msg.data_size > temp_size) ? temp_size : resp_msg.data_size);
		return resp_msg.data_size;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, resp_msg.error);
		return resp_msg.error;
	}
}
#endif

////////////////////// Multiple Spectrometer Device Function //////////////////////
INT_8S optosky_get_specified_dev_vendor(__Spectrometer_Handle spec_handle, INT_8S* vendor, INT_8U vendor_size)
{
	optosky_get_vendor_req_msg	vendor_req_msg;
	optosky_get_vendor_resp_msg vendor_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    
	memset(&vendor_req_msg, 0x00, sizeof(vendor_req_msg));
	memset(&vendor_resp_msg, 0x00, sizeof(vendor_resp_msg));
    
	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_VENDOR,
								&vendor_req_msg,
								&vendor_resp_msg);
	if(vendor_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(vendor, vendor_resp_msg.vendor , \
		   	       (vendor_resp_msg.vendor_len > vendor_size) ? vendor_size : vendor_resp_msg.vendor_len);
		return vendor_resp_msg.vendor_len;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, vendor_resp_msg.resp.error);
		return vendor_resp_msg.resp.error;
	}
}

INT_8S optosky_get_specified_dev_PN(__Spectrometer_Handle spec_handle, INT_8S* pn, INT_8U pn_size)
{
	optosky_get_pn_req_msg	pn_req_msg;
	optosky_get_pn_resp_msg pn_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    
	memset(&pn_req_msg, 0x00, sizeof(pn_req_msg));
	memset(&pn_resp_msg, 0x00, sizeof(pn_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_PN,
								&pn_req_msg,
								&pn_resp_msg);
	if(pn_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(pn, pn_resp_msg.pn, \
		   	       (pn_resp_msg.pn_len > pn_size) ? pn_size : pn_resp_msg.pn_len);
		return pn_resp_msg.pn_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, pn_resp_msg.resp.error);
		return pn_resp_msg.resp.error;
	}
}

INT_8S optosky_get_specified_dev_SN(__Spectrometer_Handle spec_handle, INT_8S* sn, INT_8U sn_size)
{
	optosky_get_sn_req_msg	sn_req_msg;
	optosky_get_sn_resp_msg sn_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&sn_req_msg, 0x00, sizeof(sn_req_msg));
	memset(&sn_resp_msg, 0x00, sizeof(sn_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_SN,
								&sn_req_msg,
								&sn_resp_msg);
	if(sn_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(sn, sn_resp_msg.sn , \
		   	       (sn_resp_msg.sn_len > sn_size) ? sn_size : sn_resp_msg.sn_len);
		return sn_resp_msg.sn_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, sn_resp_msg.resp.error);
		return sn_resp_msg.resp.error;
	}

}

INT_8S optosky_get_specified_soft_version(__Spectrometer_Handle spec_handle, INT_8S* version, INT_8U version_size)
{
	optosky_get_soft_version_req_msg	version_req_msg;
	optosky_get_soft_version_resp_msg version_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&version_req_msg, 0x00, sizeof(version_req_msg));
	memset(&version_resp_msg, 0x00, sizeof(version_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_SOFT_VER,
								&version_req_msg,
								&version_resp_msg);
	if(version_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(version, version_resp_msg.soft_version , \
		   	       (version_resp_msg.soft_version_len > version_size) ? version_size : version_resp_msg.soft_version_len);
		return version_resp_msg.soft_version_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, version_resp_msg.resp.error);
		return version_resp_msg.resp.error;
	}

}

INT_8S optosky_specified_dev_get_TEC_temperature(__Spectrometer_Handle spec_handle, INT_8S* temperature, INT_8U temperature_size)
{
	optosky_get_temperature_req_msg	temperature_req_msg;
	optosky_get_temperature_resp_msg temperature_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    
	memset(&temperature_req_msg, 0x00, sizeof(temperature_req_msg));
	memset(&temperature_resp_msg, 0x00, sizeof(temperature_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_TEC_TEMP,
								&temperature_req_msg,
								&temperature_resp_msg);
	if(temperature_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(temperature, temperature_resp_msg.temperature, \
		   	       (temperature_resp_msg.temperature_len > temperature_size) ? temperature_size : temperature_resp_msg.temperature_len);
		return temperature_resp_msg.temperature_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, temperature_resp_msg.resp.error);
		return temperature_resp_msg.resp.error;
	}
}

INT_8S optosky_get_specified_dev_version(__Spectrometer_Handle spec_handle, INT_8S* version, INT_8U version_size)
{
	optosky_get_version_req_msg	version_req_msg;
	optosky_get_version_resp_msg version_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&version_req_msg, 0x00, sizeof(version_req_msg));
	memset(&version_resp_msg, 0x00, sizeof(version_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_VER,
								&version_req_msg,
								&version_resp_msg);
	if(version_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(version, version_resp_msg.version , \
		   	       (version_resp_msg.version_len > version_size) ? version_size : version_resp_msg.version_len);
		return version_resp_msg.version_len;
	}else {
	 	MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, version_resp_msg.resp.error);
		return version_resp_msg.resp.error;
	}
}

INT_8S optosky_get_specified_dev_production_date(__Spectrometer_Handle spec_handle, INT_8S* date, INT_8U date_size)
{
	optosky_get_date_req_msg date_req_msg;
	optosky_get_date_resp_msg date_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&date_req_msg, 0x00, sizeof(date_req_msg));
	memset(&date_resp_msg, 0x00, sizeof(date_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_DATE,
								&date_req_msg,
								&date_resp_msg);
	if(date_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		memcpy(date, date_resp_msg.date , \
		   	       (date_resp_msg.date_len > date_size) ? date_size : date_resp_msg.date_len);
		return date_resp_msg.date_len;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, date_resp_msg.resp.error);
		return date_resp_msg.resp.error;
	}
}

INT_8S optosky_get_specified_dev_attributes(__Spectrometer_Handle spec_handle, __Spec_attributes *attributes)
{
	optosky_get_attributes_req_msg attr_req_msg;
	optosky_get_attributes_resp_msg attr_resp_msg;

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&attr_req_msg, 0x00, sizeof(attr_req_msg));
	memset(&attr_resp_msg, 0x00, sizeof(attr_resp_msg));

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_GET_ATTRIBUTES,
								&attr_req_msg,
								&attr_resp_msg);
	if(attr_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		*attributes = attr_resp_msg.attr;
		return 0;
	}else {
		MODULE_INFO_LOG("[%s] Command return error(%d)!\n", __FUNCTION__, attr_resp_msg.resp.error);
		return attr_resp_msg.resp.error;
	}
}

__Attr_Integral_Length optosky_get_specified_dev_integral_time_length(__Spectrometer_Handle spec_handle)
{
    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }

    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

    return optoskySpec->specInfo.attributes.integral_size;
}

__Attr_Integral_Unit optosky_get_specified_dev_integral_time_unit(__Spectrometer_Handle spec_handle)
{
    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

    return optoskySpec->specInfo.attributes.integral_unit;
}

INT_16U optosky_get_specified_dev_pixel_length(__Spectrometer_Handle spec_handle)
{
    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        MODULE_INFO_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

    return optoskySpec->specInfo.attributes.pixel_number;
}

