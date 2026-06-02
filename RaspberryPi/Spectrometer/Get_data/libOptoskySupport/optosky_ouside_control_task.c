#include "optosky_support_manager_task.h"
#include "optosky_protocol_frame_task.h"
#include "optosky_systemLog_task.h"
#include "list.h"

#include <pthread.h>
#include <stdio.h>
#include <string.h>

#define EXT_CTRL_LOG(fmt, ...)  OPTOSKY_LOG_MSG_FILE("EXT", fmt, ##__VA_ARGS__)

extern libusb_device_handle *usb_handle;
extern char optosky_interface_manager_state;
extern __Optosky_Spec optoskySpec;

////////////////////// Single Spectrometer Device Control //////////////////////
static pthread_t external_scan;
static void (*External_scan_callback)(INT_16U count, INT_16U *spectrum) = NULL;
static INT_8U optosky_exttrig_enable_flag = 0;

////////////////////// Multiple Spectrometer Device Control //////////////////////
extern struct list_head device_list;     /* Active spectrometer list */
extern INT_8U active_number;   /* Number of active spectrometer */

void optosky_external_scan_task_while(void)
{
	INT_8S ret = 0;
	int length = 0;
	static INT_32U trigCount = 0;
	INT_8U tmpBuf[10240] = {0};
	INT_16U spectrum[10240] = {0};
	INT_16U index = 0;
	
	while(1) {
		ret = libusb_bulk_transfer(usb_handle, BULK_ENDPOINT_IN, tmpBuf, 10240, &length, 1000);
		if(ret == 0) {
			if(tmpBuf[0] == 0xAA && tmpBuf[1] == 0x55) {
				if(tmpBuf[4] == 0x1E && tmpBuf[5] == 0x00) {
					trigCount++;
					if(External_scan_callback) {
						for(index=0; index<((length- 1) >> 1); index++) {
			                spectrum[index]=(tmpBuf[index*2+6]<<8) | tmpBuf[index*2+7];
			            }
						External_scan_callback(trigCount, spectrum);
					}
				}
			}
		}
	}
}

INT_8S optosky_set_external_GPIO_value(EXT_GPIO_PIN num, EXT_GPIO_VALUE value)
{
	optosky_set_outside_gpio_req_msg set_gpio_req_msg;
	optosky_set_outside_gpio_resp_msg set_gpio_resp_msg;
	INT_16U tmp = 0;
    
    if(!optosky_interface_manager_state) {
        EXT_CTRL_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&set_gpio_req_msg, 0x00, sizeof(set_gpio_req_msg));
	memset(&set_gpio_resp_msg, 0x00, sizeof(set_gpio_resp_msg));

	if(value == GPIO_VALUE_HIGH) {
		tmp = (value << num);
	}else if(value == GPIO_VALUE_LOW) {
		tmp = ~((~value) << num);
	}
    set_gpio_req_msg.control_flag = tmp;

	Optosky_excute_command_sync(&optoskySpec,
								OPTOSKY_CMD_SET_GPIO_VALUE,
								&set_gpio_req_msg,
								&set_gpio_resp_msg);
    return set_gpio_resp_msg.resp.error;
}

INT_8S optosky_external_trigger_enable(INT_16U integrationTime, void(*external_scan_callback)(INT_16U count, INT_16U *spectrum))
{
	optosky_outside_trigger_req_msg trigger_req_msg;
	optosky_outside_trigger_resp_msg trigger_resp_msg;
    
    if(!optosky_interface_manager_state) {
        EXT_CTRL_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	if(optosky_exttrig_enable_flag != 0) {
        EXT_CTRL_LOG("external trigger is already enable! in %s\n", __FUNCTION__);
		return (-1);
	}
	
	memset(&trigger_req_msg, 0x00, sizeof(trigger_req_msg));
	memset(&trigger_resp_msg, 0x00, sizeof(trigger_resp_msg));
	
    trigger_req_msg.integral_time = integrationTime;
	Optosky_excute_command_sync(&optoskySpec, 
								OPTOSKY_CMD_ENABLE_EXTTRIG,
								&trigger_req_msg,
								&trigger_resp_msg);
    if(trigger_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
        if(external_scan_callback) {
            External_scan_callback = external_scan_callback;
            INT_8S ret = pthread_create(&external_scan, NULL, (void*)optosky_external_scan_task_while, NULL);
            if(ret != 0) {
                return (-2);
            }
            optosky_exttrig_enable_flag = 1;
            return 0;
        }
    }else {
		return trigger_resp_msg.resp.error;
    }
}

INT_8S optosky_external_trigger_disable(void)
{
    if(!optosky_interface_manager_state) {
        EXT_CTRL_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	if(optosky_exttrig_enable_flag == 0) {
        EXT_CTRL_LOG("external trigger is not enable! in %s\n", __FUNCTION__);
		return (-1);
	}else {
        EXT_CTRL_LOG("external trigger is disable! in %s\n", __FUNCTION__);
		optosky_exttrig_enable_flag = 0;
		pthread_cancel(external_scan);
		return 0;
	}
}

////////////////////// Multiple Spectrometer Device Function //////////////////////
void optosky_specified_dev_external_scan_task_while(void *arg)
{
	INT_8S ret = 0;
	int length = 0;
	static INT_32U trigCount = 0;
	INT_8U tmpBuf[10240] = {0};
	INT_16U spectrum[10240] = {0};
	INT_16U index = 0;
	__Optosky_Spec *optoskySpec = (__Optosky_Spec *)arg;

	while(1) {
		ret = libusb_bulk_transfer(optoskySpec->usbHandler, BULK_ENDPOINT_IN, tmpBuf, 10240, &length, 1000);
		if(ret == 0) {
			if(tmpBuf[0] == 0xAA && tmpBuf[1] == 0x55) {
				if(tmpBuf[4] == 0x1E && tmpBuf[5] == 0x00) {
					trigCount++;
					if(optoskySpec->External_scan_callback) {
						for(index=0; index<((length- 1) >> 1); index++) {
			                spectrum[index] = (tmpBuf[index * 2 + 6]<<8) | tmpBuf[index * 2 + 7];
			            }
						optoskySpec->External_scan_callback(get_spec_handle_by_spec_control(*optoskySpec), trigCount, spectrum);
					}
				}
			}
		}
	}
}

INT_8S optosky_set_specified_dev_external_GPIO_value(__Spectrometer_Handle spec_handle, EXT_GPIO_PIN num, EXT_GPIO_VALUE value)
{
	optosky_set_outside_gpio_req_msg set_gpio_req_msg;
	optosky_set_outside_gpio_resp_msg set_gpio_resp_msg;
	INT_16U tmp = 0;
    
    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        EXT_CTRL_LOG("usb interface is not alive! in %s\n", __FUNCTION__);
        return (-10);
    }

	memset(&set_gpio_req_msg, 0x00, sizeof(set_gpio_req_msg));
	memset(&set_gpio_resp_msg, 0x00, sizeof(set_gpio_resp_msg));

	if(value == GPIO_VALUE_HIGH) {
		tmp = (value << num);
	}else if(value == GPIO_VALUE_LOW) {
		tmp = ~((~value) << num);
	}
    set_gpio_req_msg.control_flag = tmp;

	Optosky_excute_command_sync(optoskySpec,
								OPTOSKY_CMD_SET_GPIO_VALUE,
								&set_gpio_req_msg,
								&set_gpio_resp_msg);
    return set_gpio_resp_msg.resp.error;
}

INT_8S optosky_specified_dev_external_trigger_enable(__Spectrometer_Handle spec_handle, INT_16U integrationTime, void(*external_scan_callback)(__Spectrometer_Handle spec_handle,INT_16U count, INT_16U *spectrum))
{
    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        EXT_CTRL_LOG("%s usb interface is not alive! in %s\n", optoskySpec->usb_serial, __FUNCTION__);
        return (-10);
    }

	optosky_outside_trigger_req_msg trigger_req_msg;
	optosky_outside_trigger_resp_msg trigger_resp_msg;

    if(optoskySpec->externFlag) {
        EXT_CTRL_LOG("%s external trigger is already enable! in %s\n", optoskySpec->usb_serial, __FUNCTION__);
        return (-1);
    }
	
	memset(&trigger_req_msg, 0x00, sizeof(trigger_req_msg));
	memset(&trigger_resp_msg, 0x00, sizeof(trigger_resp_msg));
	
    trigger_req_msg.integral_time = integrationTime;
	Optosky_excute_command_sync(optoskySpec, 
								OPTOSKY_CMD_ENABLE_EXTTRIG,
								&trigger_req_msg,
								&trigger_resp_msg);
    if(trigger_resp_msg.resp.result == OPTOSKY_CMD_RESULT_SUCCESS) {
        if(external_scan_callback) {
            optoskySpec->External_scan_callback = external_scan_callback;
            INT_8S ret = pthread_create(&optoskySpec->pth_external, NULL, (void*)optosky_specified_dev_external_scan_task_while, (void*)optoskySpec);
            if(ret != 0) {
                return (-2);
            }
            optoskySpec->externFlag = 1;
            return 0;
        }
    }else {
		return trigger_resp_msg.resp.error;
    }
}

INT_8S optosky_specified_dev_external_trigger_disable(__Spectrometer_Handle spec_handle)
{
    if(strlen(spec_handle.sn) == 0) {
        return (-6);
    }
    __Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
    if(optoskySpec == NULL || optoskySpec->isOpen == 0) {
        EXT_CTRL_LOG("%s usb interface is not alive! in %s\n", optoskySpec->usb_serial, __FUNCTION__);
        return (-10);
    }

	if(optoskySpec->externFlag == 0) {
        EXT_CTRL_LOG("external trigger is not enable! in %s\n", __FUNCTION__);
		return (-1);
	}else {
        EXT_CTRL_LOG("external trigger is disable! in %s\n", __FUNCTION__);
		optoskySpec->externFlag = 0;
		pthread_cancel(optoskySpec->pth_external);
		return 0;
	}
}



