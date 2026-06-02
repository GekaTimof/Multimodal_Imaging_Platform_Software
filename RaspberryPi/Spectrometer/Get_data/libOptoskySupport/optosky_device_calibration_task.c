#include "optosky_protocol_frame_task.h"
#include "optosky_support_manager_task.h"
#include "optosky_systemLog_task.h"
#include <stdbool.h>



#define CALC_TASK_LOG(fmt, ...)  OPTOSKY_LOG_MSG_FILE("CALC", fmt, ##__VA_ARGS__)

extern libusb_device_handle *usb_handle;
extern char optosky_interface_manager_state;
extern __Optosky_Spec optoskySpec;
 

static FLOAT my_pow(FLOAT x, FLOAT y) {
    FLOAT result = 1.0;

    if (y == 0) {
        return 1.0;
    }

    if (y > 0) {
        for (int i = 0; i < y; i++) {
            result *= x;
        }
    }
    else {
        for (int i = 0; i > y; i--) {
            result /= x;
        }
    }

    return result;
}

static void deductDark(FLOAT original[], FLOAT *processedData, INT_16U spectrum_size, s_DARK_FACTOR *darkFactor, INT_16U integrationtime)
{
	FLOAT dark = 0;
    __Spec_attributes attributes;
	FLOAT time = integrationtime;
    optosky_get_attributes(&attributes);
	if(attributes.integral_unit == 1) // ATP2000H积分为us时暗电流处理，定标还是用ms定
		time = time / 1000;

	for (int i = 0; i < spectrum_size; i++)
	{
		dark = time* darkFactor[i].k + darkFactor[i].b;
		processedData[i] = (float)(original[i]) - dark;
	}
}

static void shapeCalibration(FLOAT *original, FLOAT *processedData, INT_16U spectrum_size, FLOAT *spcoefficient)
{
	for (int i = 0; i < spectrum_size; i++)
	{
		processedData[i] = original[i] * spcoefficient[i];

		if (processedData[i] > 0xffff) 
			processedData[i] = 0xffff;
	}
}

static void nonlinearCalibration(FLOAT *original, FLOAT *processedData, INT_16U spectrum_size, FLOAT *nlcoefficient)
{
	for (int i = 0; i < spectrum_size; i++)
	{
		float ratio = nlcoefficient[0] * my_pow(original[i], 7) + nlcoefficient[1] * my_pow(original[i], 6)
			+ nlcoefficient[2] * my_pow(original[i], 5) + nlcoefficient[3] * my_pow(original[i], 4)
			+ nlcoefficient[4] * my_pow(original[i], 3) + nlcoefficient[5] * my_pow(original[i], 2)
			+ nlcoefficient[6] * my_pow(original[i], 1) + nlcoefficient[7];

		processedData[i] = original[i] * ratio;
	}
}

INT_8S dataProcess(INT_16U *original_data, FLOAT *dataProcessed, INT_16U spectrum_size, bool isDeductDark, bool isNonlinearCorrect, bool isShapeCalibration, s_DARK_FACTOR *dkcoefficient, FLOAT *nlcoefficient, FLOAT *spcoefficient, INT_32U integrationTime)
{
	for (int i = 0; i < spectrum_size; i++) {
		dataProcessed[i] = original_data[i];
	}

    if (isDeductDark) {
		deductDark(dataProcessed, dataProcessed, spectrum_size, dkcoefficient, integrationTime);
	}

	if (isShapeCalibration) {
		shapeCalibration(dataProcessed, dataProcessed, spectrum_size, spcoefficient);
	}

	if (isNonlinearCorrect) {
		nonlinearCalibration(dataProcessed, dataProcessed, spectrum_size, nlcoefficient);
	}

	return 0;
}

INT_16S optosky_get_dark_coefficient(s_DARK_FACTOR *DarkBuf)
{
    INT_16S i = 0;
    optosky_get_dk_coefficient_req_msg dk_coeff_req_msg;
    optosky_get_dk_coefficient_resp_msg dk_coeff_resp_msg;

    if(!optosky_interface_manager_state) {
        CALC_TASK_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    memset(&dk_coeff_req_msg, 0x00, sizeof(dk_coeff_req_msg));
    memset(&dk_coeff_resp_msg, 0x00, sizeof(dk_coeff_resp_msg));
    
    dk_coeff_req_msg.number_of_coefficients = 1;
    Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_DK_COEFFICIENT,
                                &dk_coeff_req_msg,
                                &dk_coeff_resp_msg);

    while(dk_coeff_resp_msg.pack_count < dk_coeff_req_msg.send_num){
        Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_DK_COEFFICIENT,
                                &dk_coeff_req_msg,
                                &dk_coeff_resp_msg);
    }
    if(dk_coeff_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {      
        for(i=0;i<dk_coeff_resp_msg.iFactorLenth;i++){
            DarkBuf[i] = dk_coeff_resp_msg.DarkFactor[i];
        }		
        return dk_coeff_resp_msg.iFactorLenth;
    }else {     
		CALC_TASK_LOG("Get wavelength coefficient error[%d]\n", dk_coeff_resp_msg.resp.error);
        return (-1);
    }
}

INT_16S optosky_get_shape_coefficient(FLOAT *ShapeBuf)
{
    INT_16S i = 0;
    optosky_get_sp_coefficient_req_msg sp_coeff_req_msg;
    optosky_get_sp_coefficient_resp_msg sp_coeff_resp_msg;

    if(!optosky_interface_manager_state) {
        CALC_TASK_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    memset(&sp_coeff_req_msg, 0x00, sizeof(sp_coeff_req_msg));
    memset(&sp_coeff_resp_msg, 0x00, sizeof(sp_coeff_resp_msg));
    
    sp_coeff_req_msg.number_of_coefficients = 1;
    Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_SP_COEFFICIENT,
                                &sp_coeff_req_msg,
                                &sp_coeff_resp_msg);

    while(sp_coeff_resp_msg.pack_count < sp_coeff_req_msg.send_num){
        Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_SP_COEFFICIENT,
                                &sp_coeff_req_msg,
                                &sp_coeff_resp_msg);
    }
    if(sp_coeff_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {      
        for(i=0;i<sp_coeff_resp_msg.iFactorLenth;i++){
            ShapeBuf[i] = sp_coeff_resp_msg.ShapeFactor[i];
        }		
        return sp_coeff_resp_msg.iFactorLenth;
    }else {     
		CALC_TASK_LOG("Get wavelength coefficient error[%d]\n", sp_coeff_resp_msg.resp.error);
        return (-1);
    }
}


INT_16S optosky_get_nonlinearity_coefficient(FLOAT *NonlinearityBuf)
{
    INT_16S i = 0;
    optosky_get_nl_coefficient_req_msg nl_coeff_req_msg;
    optosky_get_nl_coefficient_resp_msg nl_coeff_resp_msg;    
	
    if(!optosky_interface_manager_state) {
        CALC_TASK_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    memset(&nl_coeff_req_msg, 0x00, sizeof(nl_coeff_req_msg));
    memset(&nl_coeff_resp_msg, 0x00, sizeof(nl_coeff_resp_msg));
    
    nl_coeff_req_msg.number_of_coefficients = 1;
    Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_NL_COEFFICIENT,
                                &nl_coeff_req_msg,
                                &nl_coeff_resp_msg);

    while(nl_coeff_resp_msg.pack_count < nl_coeff_req_msg.send_num){
        Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_SP_COEFFICIENT,
                                &nl_coeff_req_msg,
                                &nl_coeff_resp_msg);
    }
    if(nl_coeff_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
        for(i=0;i<nl_coeff_resp_msg.iFactorLenth;i++){
            NonlinearityBuf[i] = nl_coeff_resp_msg.LinearFactor[i];
        }		
        return nl_coeff_resp_msg.iFactorLenth;
    }else {      
		CALC_TASK_LOG("Get wavelength coefficient error[%d]\n", nl_coeff_resp_msg.resp.error);
        return (-1);
    }
}


static INT_8S optosky_get_wavelength_coefficient(FLOAT *waveLengthBuf)
{
    optosky_get_wl_coefficient_req_msg wl_coeff_req_msg;
    optosky_get_wl_coefficient_resp_msg wl_coeff_resp_msg;
	
    if(!optosky_interface_manager_state) {
        CALC_TASK_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }
    memset(&wl_coeff_req_msg, 0x00, sizeof(wl_coeff_req_msg));
    memset(&wl_coeff_resp_msg, 0x00, sizeof(wl_coeff_resp_msg));
    
    wl_coeff_req_msg.number_of_coefficients = 1;
    Optosky_excute_command_sync(&optoskySpec,
                                OPTOSKY_CMD_GET_WL_COEFFICIENT,
                                &wl_coeff_req_msg,
                                &wl_coeff_resp_msg);
    if(wl_coeff_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
		waveLengthBuf[0] = wl_coeff_resp_msg.coefficient[0];
		waveLengthBuf[1] = wl_coeff_resp_msg.coefficient[1];
		waveLengthBuf[2] = wl_coeff_resp_msg.coefficient[2];
		waveLengthBuf[3] = wl_coeff_resp_msg.coefficient[3];
        return 0;
    }else {
		CALC_TASK_LOG("Get wavelength coefficient error[%d]\n", wl_coeff_resp_msg.resp.error);
        return (wl_coeff_resp_msg.resp.error);
    }
}

INT_16S optosky_get_wavelength_of_the_spec(FLOAT *wavelength ,INT_16U size)
{
    INT_16S index = 0;
	FLOAT coefficient[4] = {0};

    INT_8S ret = optosky_get_wavelength_coefficient(coefficient);
    if(ret == 0) {
		INT_16U ret_size = optoskySpec.specInfo.attributes.pixel_number > size ? \
							size : optoskySpec.specInfo.attributes.pixel_number;

		for(; index < ret_size; index++) {
			wavelength[index] = (FLOAT)(coefficient[0]*index*index*index) + \
								(FLOAT)(coefficient[1]*index*index) + \
								(FLOAT)(coefficient[2]*index) + \
								(FLOAT)(coefficient[3]);
		}
        //printf("pixel : %d\n", optoskySpec.specInfo.attributes.pixel_number);
		return optoskySpec.specInfo.attributes.pixel_number;
    }else {
        return ret;
    }
}

////////////////////// Multiple Spectrometer Device Function //////////////////////
static INT_8S optosky_get_specified_dev_wavelength_coefficient(__Optosky_Spec *optoskySpec, FLOAT *waveLengthBuf)
{
    optosky_get_wl_coefficient_req_msg wl_coeff_req_msg;
    optosky_get_wl_coefficient_resp_msg wl_coeff_resp_msg;
    
    memset(&wl_coeff_req_msg, 0x00, sizeof(wl_coeff_req_msg));
    memset(&wl_coeff_resp_msg, 0x00, sizeof(wl_coeff_resp_msg));
    
    wl_coeff_req_msg.number_of_coefficients = 1;
    Optosky_excute_command_sync(optoskySpec,
                                OPTOSKY_CMD_GET_WL_COEFFICIENT,
                                &wl_coeff_req_msg,
                                &wl_coeff_resp_msg);
    if(wl_coeff_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
        waveLengthBuf[0] = wl_coeff_resp_msg.coefficient[0];
        waveLengthBuf[1] = wl_coeff_resp_msg.coefficient[1];
        waveLengthBuf[2] = wl_coeff_resp_msg.coefficient[2];
        waveLengthBuf[3] = wl_coeff_resp_msg.coefficient[3];
        return 0;
    }else {
        CALC_TASK_LOG("Get wavelength coefficient error[%d]\n", wl_coeff_resp_msg.resp.error);
        return (wl_coeff_resp_msg.resp.error);
    }
}

INT_16S optosky_get_specified_dev_wavelength_of_the_spec(__Spectrometer_Handle spec_handle, FLOAT *wavelength ,INT_16U size)
{
    INT_16S index = 0;
    FLOAT coefficient[4] = {0};

    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        CALC_TASK_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

    INT_8S ret = optosky_get_specified_dev_wavelength_coefficient(optoskySpec, coefficient);
    if(ret == 0) {
        INT_16U ret_size = optoskySpec->specInfo.attributes.pixel_number > size ? \
                            size : optoskySpec->specInfo.attributes.pixel_number;

        for(; index < ret_size; index++) {
            wavelength[index] = (FLOAT)(coefficient[0]*index*index*index) + \
                                (FLOAT)(coefficient[1]*index*index) + \
                                (FLOAT)(coefficient[2]*index) + \
                                (FLOAT)(coefficient[3]);
        }
        return optoskySpec->specInfo.attributes.pixel_number;
    }else {
        return ret;
    }
}

