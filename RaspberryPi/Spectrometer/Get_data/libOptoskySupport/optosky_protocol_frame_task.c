#include "optosky_protocol_frame_task.h"

#define PROTOCOL_HAND_LOG(fmt, ...)	OPTOSKY_LOG_MSG_FILE("PROTOCOL", fmt, ##__VA_ARGS__)

extern libusb_device_handle *usb_handler;
extern __Optosky_Spec optoskySpec;

static INT_8U tmpBuf[10240] = {OPTOSKY_FRAME_HEAD_1, OPTOSKY_FRAME_HEAD_2};
static INT_16U data_length = 0;

static INT_8S optosky_usb_transfer(libusb_device_handle *usb_handler, INT_8U *transBuf, INT_8U size)
{
    int length = 0;
	
	INT_8S ret = libusb_bulk_transfer(usb_handler, BULK_ENDPOINT_OUT, transBuf, size, &length, TRANS_TIMEOUT);
	if(ret != 0) {
		return (-1);
	}else {
		return length;
	}
}

static INT_8S optosky_usb_receive(libusb_device_handle *usb_handler, INT_8U *rcvBuf)
{
	int length = 0;
	
	INT_8S ret = libusb_bulk_transfer(usb_handler, BULK_ENDPOINT_IN, rcvBuf, 10240, &length, TRANS_TIMEOUT);
	if(ret != 0) {
		return (-1);
	}else {
		return length;
	}

}

INT_8S optosky_cmd_request(libusb_device_handle *usb_handler, INT_8U cmd_id, INT_8U *para, INT_8U size)
{
	INT_8U index = 0;
	INT_32U checkSum = 0;
	INT_8U transBuf[1024];

	transBuf[0] = OPTOSKY_FRAME_HEAD_1;
	transBuf[1] = OPTOSKY_FRAME_HEAD_2;
	transBuf[2] = ((size + 4) >> 8);
	transBuf[3] = (size + 4) & 0xFF;
	transBuf[4] = cmd_id;

	for(; index<size; index++) {
		transBuf[index + 5] = para[index];
	}

	for(index=0; index<size+3; index++) {
		checkSum += transBuf[index + 2];
	}
	transBuf[index + 2] = checkSum;

	optosky_usb_transfer(usb_handler, transBuf, size + 6);
}


INT_8S optosky_cmd_response(libusb_device_handle *usb_handler, INT_8U *rcvBuf, INT_16U *size)
{
	INT_8S ret = optosky_usb_receive(usb_handler, rcvBuf);
	if(ret == -1) {
		return (ret);
	}
}

static void optosky_cmd_rcv_GetVendor_handler(optosky_get_vendor_resp_msg *resp_msg)
{
    resp_msg->vendor_len = data_length;
    memcpy(resp_msg->vendor, tmpBuf+5, data_length);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetPN_handler(optosky_get_pn_resp_msg *resp_msg)
{
    resp_msg->pn_len = data_length;
    memcpy(resp_msg->pn, tmpBuf+5, data_length);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetSN_handler(optosky_get_sn_resp_msg *resp_msg)
{
    resp_msg->sn_len = data_length;
    memcpy(resp_msg->sn, tmpBuf+5, data_length);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetTEC_TEMP_handler(optosky_get_temperature_resp_msg* resp_msg)
{
    resp_msg->temperature_len = data_length;
    memcpy(resp_msg->temperature, tmpBuf+5, data_length);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetVersion_handler(optosky_get_version_resp_msg *resp_msg)
{
    resp_msg->version_len = data_length;
    memcpy(resp_msg->version, tmpBuf+5, data_length);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetSoftVersion_handler(optosky_get_soft_version_resp_msg *resp_msg)
{
    resp_msg->soft_version_len = data_length - 1;
    memcpy(resp_msg->soft_version, tmpBuf+6, data_length - 1);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetDate_handler(optosky_get_date_resp_msg *resp_msg)
{
    resp_msg->date_len = data_length;
    memcpy(resp_msg->date, tmpBuf+5, data_length);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetAttributes_handler(optosky_get_attributes_resp_msg *resp_msg)
{
    INT_32U spec_attributes = ((tmpBuf[5] << 24) | (tmpBuf[6] << 16) | (tmpBuf[7] << 8) | (tmpBuf[8]));
    resp_msg->attr.integral_size = (spec_attributes & INTEGRAL_SIZE_MASK) ? \
                                                                IntegralTime_Size_32 : IntegralTime_Size_16;
    resp_msg->attr.integral_unit = (spec_attributes & INTEGRAL_UNIT_MASK) ? \
                                                                IntegralTime_Unit_us : IntegralTime_Unit_ms;
    resp_msg->attr.checkSum_type = (spec_attributes & CHECKSUM_BIT_MASK) ? \
                                                                Without_CheckBit : Include_CheckBit;
    resp_msg->attr.pixel_number = (spec_attributes >> 16);
    resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_GetDkCoefficient_handler(optosky_get_dk_coefficient_req_msg *req_msg,optosky_get_dk_coefficient_resp_msg *resp_msg)
{
    INT_16U i = 0;
    INT_16U size = 0;
    INT_16U last_count = 0;
    INT_8U* pt = 0;
    
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) { 
        resp_msg->pack_count = tmpBuf[5]<<8 |tmpBuf[6];      
        if(req_msg->number_of_coefficients == resp_msg->pack_count){
            if(resp_msg->pack_count == 1){   
                pt = (INT_8U*)&resp_msg->DarkFactor[0];                                             
                resp_msg->iByteSize = tmpBuf[7]<<24 | tmpBuf[8]<<16 | tmpBuf[9]<<8 |tmpBuf[10];  
                resp_msg->iFactorLenth = tmpBuf[20]<<24 | tmpBuf[19]<<16 | tmpBuf[18]<<8 |tmpBuf[17];           
                if (resp_msg->iByteSize % 512){
					req_msg->send_num = resp_msg->iByteSize / 512 + 1;
				}
				else{
					req_msg->send_num = resp_msg->iByteSize / 512;
				}
                if(resp_msg->iByteSize > 498){               
                    for(i=0; i<498; i++){
                        *pt = tmpBuf[21+i];                     
                        pt++;
                        
                    }
                    req_msg->number_of_coefficients++;
                }else{
                    for(i=0; i<resp_msg->iByteSize-14; i++){
                        *pt = tmpBuf[21+i];                     
                        pt++;
                        
                    }
                }
            }else if(resp_msg->pack_count > 1){
                pt = (INT_8U*)&resp_msg->DarkFactor[0] + 498*1 + (resp_msg->pack_count - 2)*512;
                if(resp_msg->pack_count == req_msg->send_num){
                    last_count = (resp_msg->iByteSize - 14) - 498 - (resp_msg->pack_count - 2)*512;
                    for(i=0; i<last_count; i++){
                        *pt = tmpBuf[7+i];                     
                        pt++;                       
                    }
                }else{
                    for(i=0; i<512; i++){
                        *pt = tmpBuf[7+i];                     
                        pt++;                        
                    }
					req_msg->number_of_coefficients++;
                }
            }
        }
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_GetSpCoefficient_handler(optosky_get_sp_coefficient_req_msg *req_msg,optosky_get_sp_coefficient_resp_msg *resp_msg)
{
    INT_16U i = 0;
    INT_16U size = 0;
    INT_16U last_count = 0;
    INT_8U* pt = 0;
    
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) { 
        resp_msg->pack_count = tmpBuf[5]<<8 |tmpBuf[6];      
        if(req_msg->number_of_coefficients == resp_msg->pack_count){
            if(resp_msg->pack_count == 1){   
                pt = (INT_8U*)&resp_msg->ShapeFactor[0];                                             
                resp_msg->iByteSize = tmpBuf[7]<<24 | tmpBuf[8]<<16 | tmpBuf[9]<<8 |tmpBuf[10];  
                resp_msg->iFactorLenth = tmpBuf[20]<<24 | tmpBuf[19]<<16 | tmpBuf[18]<<8 |tmpBuf[17];           
                if (resp_msg->iByteSize % 512){
					req_msg->send_num = resp_msg->iByteSize / 512 + 1;
				}
				else{
					req_msg->send_num = resp_msg->iByteSize / 512;
				}
                if(resp_msg->iByteSize > 498){               
                    for(i=0; i<498; i++){
                        *pt = tmpBuf[21+i];                     
                        pt++;
                        
                    }
                    req_msg->number_of_coefficients++;
                }else{
                    for(i=0; i<resp_msg->iByteSize-14; i++){
                        *pt = tmpBuf[21+i];                     
                        pt++;
                        
                    }
                }
            }else if(resp_msg->pack_count > 1){
                pt = (INT_8U*)&resp_msg->ShapeFactor[0] + 498*1 + (resp_msg->pack_count - 2)*512;
                if(resp_msg->pack_count == req_msg->send_num){
                    last_count = (resp_msg->iByteSize - 14) - 498 - (resp_msg->pack_count - 2)*512;
                    for(i=0; i<last_count; i++){
                        *pt = tmpBuf[7+i];                     
                        pt++;                       
                    }
                }else{
                    for(i=0; i<512; i++){
                        *pt = tmpBuf[7+i];                     
                        pt++;                        
                    }
					req_msg->number_of_coefficients++;
                }
            }
        }
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_GetNlCoefficient_handler(optosky_get_nl_coefficient_req_msg *req_msg,optosky_get_nl_coefficient_resp_msg *resp_msg)
{
    INT_16U i = 0;
    INT_16U size = 0;
    INT_16U last_count = 0;
    INT_8U* pt = 0;

    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) { 
        resp_msg->pack_count = tmpBuf[5]<<8 |tmpBuf[6];      
        if(req_msg->number_of_coefficients == resp_msg->pack_count){
            if(resp_msg->pack_count == 1){   
                pt = (INT_8U*)&resp_msg->LinearFactor[0];                                             
                resp_msg->iByteSize = tmpBuf[7]<<24 | tmpBuf[8]<<16 | tmpBuf[9]<<8 |tmpBuf[10];  
                resp_msg->iFactorLenth = tmpBuf[20]<<24 | tmpBuf[19]<<16 | tmpBuf[18]<<8 |tmpBuf[17];           
                if (resp_msg->iByteSize % 512){
					req_msg->send_num = resp_msg->iByteSize / 512 + 1;
				}
				else{
					req_msg->send_num = resp_msg->iByteSize / 512;
				}
                if(resp_msg->iByteSize > 498){               
                    for(i=0; i<498; i++){
                        *pt = tmpBuf[21+i];                     
                        pt++;
                        
                    }
                    req_msg->number_of_coefficients++;
                }else{
                    for(i=0; i<resp_msg->iByteSize-14; i++){
                        *pt = tmpBuf[21+i];                     
                        pt++;
                        
                    }
                }
            }else if(resp_msg->pack_count > 1){
                pt = (INT_8U*)&resp_msg->LinearFactor[0] + 498*1 + (resp_msg->pack_count - 2)*512;
                if(resp_msg->pack_count == req_msg->send_num){
                    last_count = (resp_msg->iByteSize - 14) - 498 - (resp_msg->pack_count - 2)*512;
                    for(i=0; i<last_count; i++){
                        *pt = tmpBuf[7+i];                     
                        pt++;                       
                    }
                }else{
                    for(i=0; i<512; i++){
                        *pt = tmpBuf[7+i];                     
                        pt++;                        
                    }
					req_msg->number_of_coefficients++;
                }
            }
        }
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
    // union {
    //     float f;    
    //     unsigned int h;    
    // }utemp;
    // if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
    //     resp_msg->iByteSize = tmpBuf[7]<<24 | tmpBuf[8]<<16 | tmpBuf[9]<<8 |tmpBuf[10];
    //     resp_msg->iFactorLenth = tmpBuf[20]<<24 | tmpBuf[19]<<16 | tmpBuf[18]<<8 |tmpBuf[17];
        
    //     for(; i<resp_msg->iFactorLenth; i++) {
    //         utemp.h = tmpBuf[24+i*4]<<24 | tmpBuf[23+i*4]<<16 | tmpBuf[22+i*4]<<8 |tmpBuf[21+i*4];
    //         resp_msg->LinearFactor[i] = utemp.f;  
    //     }
    //     resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    // }else {
    //     resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
    //     resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    // }
}

static void optosky_cmd_rcv_GetWlCoefficient_handler(optosky_get_wl_coefficient_resp_msg *resp_msg)
{
    INT_8U index = 0;
    
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        INT_8U coef_tmp[4][4] = {0};
        for(index=0; index<4; index++) {
            coef_tmp[0][index] = tmpBuf[index + 5 + 16];
            coef_tmp[1][index] = tmpBuf[index + 5 + 16 + 4];
            coef_tmp[2][index] = tmpBuf[index + 5 + 16 + 8];
            coef_tmp[3][index] = tmpBuf[index + 5 + 16 + 12];
        }
        resp_msg->coefficient[0] = *(FLOAT*)coef_tmp[0];
        resp_msg->coefficient[1] = *(FLOAT*)coef_tmp[1];
        resp_msg->coefficient[2] = *(FLOAT*)coef_tmp[2];
        resp_msg->coefficient[3] = *(FLOAT*)coef_tmp[3];
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_getIntegralTime_handler(optosky_get_integral_time_resp_msg *resp_msg)
{
    if(data_length == 0x04) {
        resp_msg->integral_time = (tmpBuf[5] << 24) | (tmpBuf[6] << 16) | \
								   (tmpBuf[7] << 8) | (tmpBuf[8]);
    }else {
		resp_msg->integral_time = (tmpBuf[5] << 8) | (tmpBuf[6]);
    }
	resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
}

static void optosky_cmd_rcv_SetIntegralTime_handler(optosky_set_integral_time_resp_msg *resp_msg)
{
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_SetAverage_handler(optosky_set_average_resp_msg *resp_msg)
{
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <stdlib.h>

static void optosky_cmd_rcv_ScanSync_handler(optosky_spectrum_control_resp_msg *resp_msg)
{
    INT_16U index = 0;

    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        for(index=0; index<((data_length-1)>>1); index++) {
            resp_msg->spectrum[index] = (tmpBuf[index * 2 + OPTOSKY_FRAME_DATA_OFF + 1] << 8) | \
                                         tmpBuf[index * 2 + OPTOSKY_FRAME_DATA_OFF + 2];
        }
        resp_msg->pixel_length = ((data_length - 1) >> 1);
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_ScanAsync_handler(optosky_spectrum_control_resp_msg *resp_msg)
{
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_GetAsyncData_handler(optosky_spectrum_control_resp_msg *resp_msg)
{
    INT_16U index = 0;
    
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        for(index=0; index<((data_length-1)>>1); index++) {
            resp_msg->spectrum[index] = (tmpBuf[index*2+OPTOSKY_FRAME_DATA_OFF+1]<<8) | \
                                         tmpBuf[index*2+OPTOSKY_FRAME_DATA_OFF+2];
        }
        resp_msg->pixel_length = ((data_length - 1) >> 1);
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_SetGPIO_handler(optosky_set_outside_gpio_resp_msg *resp_msg)
{
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

static void optosky_cmd_rcv_EnableExtTrig_handler(optosky_outside_trigger_resp_msg *resp_msg)
{
    if(tmpBuf[OPTOSKY_FRAME_DATA_OFF] == 0x00) {
        resp_msg->resp.result = OPTOSKY_CMD_RESULT_SUCCESS;
    }else {
       resp_msg->resp.result = OPTOSKY_CMD_RESULT_FAILURE;
       resp_msg->resp.error = OPTOSKY_CMD_ERR_DATA_ERROR;
    }
}

void Optosky_excute_command_sync(__Optosky_Spec *optoskySpec,
								 INT_8U CMD_ID,
								 void *req_msg,
								 void *resp_msg)
{
	INT_8S ret = 0;
	INT_32U length = 0;
	INT_32U checkSum = 0;
	INT_16U index = 0;
	INT_16U tmpBuf_len = 0;
	INT_32U integral_time = 0;

    data_length = 0;
	tmpBuf[OPTOSKY_FRAME_CMD_OFF] = CMD_ID;
	switch(CMD_ID)
	{
	case OPTOSKY_CMD_GET_VENDOR:
	case OPTOSKY_CMD_GET_PN:
	case OPTOSKY_CMD_GET_SN:
	case OPTOSKY_CMD_GET_VER:
	case OPTOSKY_CMD_GET_DATE:
	case OPTOSKY_CMD_GET_BOARD_TEMP:
	case OPTOSKY_CMD_GET_TEC_TEMP:
	case OPTOSKY_CMD_GET_ATTRIBUTES:
	case OPTOSKY_CMD_GET_SOFT_VER:
    case OPTOSKY_CMD_GET_SCAN_TIME:
    case OPTOSKY_CMD_GET_ASYNC_SPECTRUM_DATA:{
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x04;
        data_length = 3;
        tmpBuf[data_length + 2] = 0;
        for(index=0; index<data_length; index++) {
            tmpBuf[data_length+2] += tmpBuf[index + 2];
        }
        tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_GET_DK_COEFFICIENT:{
        optosky_get_dk_coefficient_req_msg *req_tmp = (optosky_get_dk_coefficient_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
		tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->number_of_coefficients >> 8);
		tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (req_tmp->number_of_coefficients & 0xFF);
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
		for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_GET_SP_COEFFICIENT:{
        optosky_get_sp_coefficient_req_msg *req_tmp = (optosky_get_sp_coefficient_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
		tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->number_of_coefficients >> 8);
		tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (req_tmp->number_of_coefficients & 0xFF);
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
		for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_GET_NL_COEFFICIENT:{
        optosky_get_nl_coefficient_req_msg *req_tmp = (optosky_get_nl_coefficient_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
		tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->number_of_coefficients >> 8);
		tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (req_tmp->number_of_coefficients & 0xFF);
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
		for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;
	case OPTOSKY_CMD_GET_WL_COEFFICIENT:{
        optosky_get_wl_coefficient_req_msg *req_tmp = (optosky_get_wl_coefficient_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
		tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->number_of_coefficients >> 8);
		tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (req_tmp->number_of_coefficients & 0xFF);
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
		for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_SET_GPIO_VALUE:{
        optosky_set_outside_gpio_req_msg *req_tmp = (optosky_set_outside_gpio_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
        tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->control_flag >> 8);
		tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = req_tmp->control_flag & 0xFF;
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
        for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
        }
		tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_ENABLE_EXTTRIG:{
        optosky_outside_trigger_req_msg *req_tmp = (optosky_outside_trigger_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
        tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->integral_time >> 8);
        tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = req_tmp->integral_time & 0xFF;
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
        for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_SET_SCAN_TIME:{
        optosky_set_integral_time_req_msg *req_tmp = (optosky_set_integral_time_req_msg*)req_msg;
        if(optoskySpec->specInfo.attributes.integral_size == IntegralTime_Size_16) {
            tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
    		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
            tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->integral_time >> 8);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = req_tmp->integral_time & 0xFF;
            data_length = 5;
        }else {
            tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
    		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x08;
            tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->integral_time >> 24);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (req_tmp->integral_time >> 16);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 2] = (req_tmp->integral_time >> 8);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 3] = req_tmp->integral_time & 0xFF;
            data_length = 7;
        }
        tmpBuf[data_length + 2] = 0;
        for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;

    case OPTOSKY_CMD_SET_AVERAGE:{
        optosky_set_average_req_msg *req_tmp = (optosky_set_average_req_msg*)req_msg;
        tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
        tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->average >> 8);
        tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = req_tmp->average & 0xFF;
        data_length = 5;
        tmpBuf[data_length + 2] = 0;
        for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
    }break;
    case OPTOSKY_CMD_GET_DARK_SYNC:
    case OPTOSKY_CMD_GET_SPECTRUM_SYNC:
    case OPTOSKY_CMD_GET_DARK_ASYNC:
    case OPTOSKY_CMD_GET_SPECTRUM_ASYNC:{
        optosky_spectrum_control_req_msg *req_tmp = (optosky_spectrum_control_req_msg*)req_msg;
        if(optoskySpec->specInfo.attributes.integral_size == IntegralTime_Size_16) {
            tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
    		tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x06;
            tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->integral_time >> 8);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = req_tmp->integral_time & 0xFF;
            data_length = 5;
        }else {
            tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] = 0;
            tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1] = 0x08;
            tmpBuf[OPTOSKY_FRAME_DATA_OFF] = (req_tmp->integral_time >> 24);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 1] = (req_tmp->integral_time >> 16);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 2] = (req_tmp->integral_time >> 8);
            tmpBuf[OPTOSKY_FRAME_DATA_OFF + 3] = req_tmp->integral_time & 0xFF;
            data_length = 7;
        }
        tmpBuf[data_length + 2] = 0;
        for(index=0; index<data_length; index++) {
			tmpBuf[data_length + 2] += tmpBuf[index + 2];
		}
		tmpBuf_len = data_length + 3;
        /* Judge receiving time. */
        if(optoskySpec->specInfo.attributes.integral_unit == IntegralTime_Unit_us) {
            integral_time = req_tmp->integral_time/1000 + 1;
        }else {
            integral_time = req_tmp->integral_time;
        }
    }break;
    default:{
        optosky_resp_v01 *resp_tmp = (optosky_resp_v01*)resp_msg;
		resp_tmp->result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_tmp->error = OPTOSKY_CMD_ERR_CMD_INVALID;
		return ;
    }break;
	}

    ret = libusb_bulk_transfer(optoskySpec->usbHandler, BULK_ENDPOINT_OUT, tmpBuf, tmpBuf_len, &length, TRANS_TIMEOUT);
	if(ret != 0) {
        optosky_resp_v01 *resp_tmp = (optosky_resp_v01*)resp_msg;
		resp_tmp->result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_tmp->error = OPTOSKY_CMD_ERR_TRANSFER_TIMEOUT;
		return ;
	}

	ret = libusb_bulk_transfer(optoskySpec->usbHandler, BULK_ENDPOINT_IN, tmpBuf, 10240, &length, (TRANS_TIMEOUT + integral_time));
	if(ret == 0) {
		if(tmpBuf[OPTOSKY_FRAME_HEAD_OFF] == 0xAA && tmpBuf[OPTOSKY_FRAME_HEAD_OFF + 1] == 0x55) {
			if(tmpBuf[OPTOSKY_FRAME_CMD_OFF] == CMD_ID) {
				data_length = ((tmpBuf[OPTOSKY_FRAME_LENGTH_OFF] << 8) | tmpBuf[OPTOSKY_FRAME_LENGTH_OFF + 1]) - 4;
				switch(CMD_ID)
				{
				/*=============================== INFOMATION ===============================*/
				case OPTOSKY_CMD_GET_VENDOR:{
                    optosky_cmd_rcv_GetVendor_handler((optosky_get_vendor_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_PN:{
                    optosky_cmd_rcv_GetPN_handler((optosky_get_pn_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_SN:{
                    optosky_cmd_rcv_GetSN_handler((optosky_get_sn_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_TEC_TEMP:{
                    optosky_cmd_rcv_GetTEC_TEMP_handler((optosky_get_temperature_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_VER:{
                    optosky_cmd_rcv_GetVersion_handler((optosky_get_version_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_SOFT_VER:{
                    optosky_cmd_rcv_GetSoftVersion_handler((optosky_get_soft_version_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_DATE:{
                    optosky_cmd_rcv_GetDate_handler((optosky_get_date_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_ATTRIBUTES:{
                    optosky_cmd_rcv_GetAttributes_handler((optosky_get_attributes_resp_msg*)resp_msg);
				}break;
				/*=============================== CALIBRATION ===============================*/
                case OPTOSKY_CMD_GET_DK_COEFFICIENT:{
                    optosky_cmd_rcv_GetDkCoefficient_handler((optosky_get_dk_coefficient_req_msg*)req_msg,(optosky_get_dk_coefficient_resp_msg*)resp_msg);
				}break;
                case OPTOSKY_CMD_GET_SP_COEFFICIENT:{
                    optosky_cmd_rcv_GetSpCoefficient_handler((optosky_get_sp_coefficient_req_msg*)req_msg,(optosky_get_sp_coefficient_resp_msg*)resp_msg);
				}break;
                case OPTOSKY_CMD_GET_NL_COEFFICIENT:{
                    optosky_cmd_rcv_GetNlCoefficient_handler((optosky_get_nl_coefficient_req_msg*)req_msg,(optosky_get_nl_coefficient_resp_msg*)resp_msg);
				}break;
				case OPTOSKY_CMD_GET_WL_COEFFICIENT:{
                    optosky_cmd_rcv_GetWlCoefficient_handler((optosky_get_wl_coefficient_resp_msg*)resp_msg);
				}break;
				/*=============================== SCANNING SPECTROMETER ===============================*/
                case OPTOSKY_CMD_GET_SCAN_TIME:{
                    optosky_cmd_rcv_getIntegralTime_handler((optosky_get_integral_time_resp_msg*)resp_msg);                    
				}break;
                case OPTOSKY_CMD_SET_SCAN_TIME:{
                    optosky_cmd_rcv_SetIntegralTime_handler((optosky_set_integral_time_resp_msg*)resp_msg);
                }break;
                case OPTOSKY_CMD_SET_AVERAGE:{
                    optosky_cmd_rcv_SetAverage_handler((optosky_set_average_resp_msg*)resp_msg);
                }break;
                case OPTOSKY_CMD_GET_DARK_SYNC:
                case OPTOSKY_CMD_GET_SPECTRUM_SYNC:{
                    optosky_cmd_rcv_ScanSync_handler((optosky_spectrum_control_resp_msg*)resp_msg);
                }break;
                case OPTOSKY_CMD_GET_DARK_ASYNC:
                case OPTOSKY_CMD_GET_SPECTRUM_ASYNC:{
                    optosky_cmd_rcv_ScanAsync_handler((optosky_spectrum_control_resp_msg*)resp_msg);
                }break;
                case OPTOSKY_CMD_GET_ASYNC_SPECTRUM_DATA:{
                    optosky_cmd_rcv_GetAsyncData_handler((optosky_spectrum_control_resp_msg*)resp_msg);
                }break;
				/*=============================== OUTSIDE CONTROL ===============================*/
                case OPTOSKY_CMD_SET_GPIO_VALUE:{
                    optosky_cmd_rcv_SetGPIO_handler((optosky_set_outside_gpio_resp_msg*)resp_msg);
                }break;
                case OPTOSKY_CMD_ENABLE_EXTTRIG
:{
                    optosky_cmd_rcv_EnableExtTrig_handler((optosky_outside_trigger_resp_msg*)resp_msg);
                }break;
                }
			}else {
    			optosky_resp_v01 *resp_tmp = (optosky_resp_v01*)resp_msg;
				resp_tmp->result = OPTOSKY_CMD_RESULT_FAILURE;
                resp_tmp->error = OPTOSKY_CMD_ERR_CMD_INVALID;
				return ;
			}
		}
	}else {
        optosky_resp_v01 *resp_tmp = (optosky_resp_v01*)resp_msg;
		resp_tmp->result = OPTOSKY_CMD_RESULT_FAILURE;
        resp_tmp->error = OPTOSKY_CMD_ERR_RECEIVE_TIMEOUT;
		return ;
    }
}


