#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include "optosky_support_manager_task.h"
#include "optosky_systemLog_task.h"

#define SUPPORT_MANA_LOG(fmt, ...)	OPTOSKY_LOG_MSG_FILE("MANA", fmt, ##__VA_ARGS__)
#define CHR_MAX_SIZE    128
#define SPEC_NUMBER_MAX 10

extern INT_8S optosky_get_attributes(__Spec_attributes *attributes);

////////////////////// Single Spectrometer Device Control //////////////////////
libusb_device_handle *usb_handle;   /* libusb handle. */
char optosky_interface_manager_state = 0;   /* device enable flag. */
__Optosky_Spec optoskySpec;         /* spectrometer devices. */

////////////////////// Multiple Spectrometer Device Control //////////////////////
LIST_HEAD(device_list);     /* Active spectrometer list */
INT_8U active_number = 0;   /* Number of active spectrometer */
libusb_device_handle *usb_handles[SPEC_NUMBER_MAX];
__Optosky_Spec optoskySpecs[SPEC_NUMBER_MAX];         /* spectrometer devices. */
__Spectrometer_Handle spec_handle_tmp;

__Optosky_Spec *get_spec_control_by_spec_handle(__Spectrometer_Handle spec_handle)
{
	INT_8S index = 0;

	for (; index < SPEC_NUMBER_MAX; index++) {
		if (!strncmp(optoskySpecs[index].usb_serial, spec_handle.sn, 16)) {
			return &optoskySpecs[index];
		}
	}
	if (optosky_interface_manager_state == 1) {
		if (!strncmp(optoskySpec.usb_serial, spec_handle.sn, 16)) {
			return &optoskySpec;
		}
	}
	return NULL;
}

__Spectrometer_Handle get_spec_handle_by_spec_control(__Optosky_Spec optoskySpec)
{
	memcpy(spec_handle_tmp.sn, optoskySpec.usb_serial, CHR_MAX_SIZE);
	return spec_handle_tmp;
}

void optosky_debug_list_devices(void)
{
	INT_8U index = 0;
	struct list_head *pos;

	printf("=====================================================\n");
	__list_for_each(pos, &device_list) {
		__Optosky_Spec *optoskySpec = list_entry(pos, __Optosky_Spec, node);
		printf("%s\t|%s\t|%s\n", \
			optoskySpec->specInfo.dev_model, \
			optoskySpec->usb_serial, \
			get_spec_handle_by_spec_control(optoskySpecs[index]).sn);
	}
	/*
		for(; index<SPEC_NUMBER_MAX; index++) {
			printf("[%d]\t", index);
			if(optoskySpecs[index].isOpen == 1) {
				printf("==>%s  |  %s  |  %s  |time size:%d |time unit:%d | checkSum:%d", \
						optoskySpecs[index].specInfo.dev_model, \
						optoskySpecs[index].specInfo.serial_number, \
						get_spec_handle_by_spec_control(optoskySpecs[index]).sn, \
						optoskySpecs[index].specInfo.attributes.integral_size,
						optoskySpecs[index].specInfo.attributes.integral_unit,
						optoskySpecs[index].specInfo.attributes.checkSum_type,);
			}
			printf("\n");
		}
	*/
}

static void optosky_get_device_infomation(__Optosky_Spec *optoskySpec)
{
	INT_8S ret = 0;
	INT_8U serialBuf[128] = { 0 };
	struct libusb_device_descriptor desc;

	libusb_get_device_descriptor(libusb_get_device(optoskySpec->usbHandler), &desc);
	libusb_get_string_descriptor_ascii(optoskySpec->usbHandler, desc.iSerialNumber, optoskySpec->usb_serial, CHR_MAX_SIZE);

	/* 1.Get The device attributes. */
	ret = optosky_get_specified_dev_attributes(get_spec_handle_by_spec_control(*optoskySpec), &optoskySpec->specInfo.attributes);
	if (ret == 0) {
		ret = optosky_get_specified_dev_PN(get_spec_handle_by_spec_control(*optoskySpec), optoskySpec->specInfo.dev_model, 8);
		if (ret < 0) {
			SUPPORT_MANA_LOG("Get PN failed!!\n");
			return;
		}
		if (optoskySpec->specInfo.attributes.pixel_number == 0) {
			goto pixel_number_set;
			/*			if(!strncmp(optoskySpec->specInfo.dev_model, "ATP2002", 7)) {
							optoskySpec->specInfo.attributes.pixel_number = 2048;
						}else {
							optoskySpec->specInfo.attributes.pixel_number = 2048;
						}
			*/
		}
	}
	else {	/* without the get device attributes interface. */
	   /********* 1 Get module PN  *********/
		ret = optosky_get_specified_dev_PN(get_spec_handle_by_spec_control(*optoskySpec), optoskySpec->specInfo.dev_model, 8);
		if (ret < 0) {
			SUPPORT_MANA_LOG("Get PN failed!\n");
			return;
		}
		optoskySpec->specInfo.attributes.integral_size = IntegralTime_Size_16;
		optoskySpec->specInfo.attributes.integral_unit = IntegralTime_Unit_ms;
		optoskySpec->specInfo.attributes.checkSum_type = Include_CheckBit;
	pixel_number_set:
		if (!strncmp(optoskySpec->specInfo.dev_model, "ATP1", 4)) {
			if (!strncmp(optoskySpec->specInfo.dev_model, "ATP1010", 7)) {
				optoskySpec->specInfo.attributes.pixel_number = 512;
			}
			else {
				optoskySpec->specInfo.attributes.pixel_number = 1024;
			}
		}
		else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP2", 4)) {
			if (!strncmp(optoskySpec->specInfo.dev_model, "ATP2100", 7)) {
				optoskySpec->specInfo.attributes.pixel_number = 512;
			}
			else {
				optoskySpec->specInfo.attributes.pixel_number = 2048;
			}
			if (!strncmp(optoskySpec->specInfo.dev_model, "ATP2002H", 8)) {
				optoskySpec->specInfo.attributes.integral_size = IntegralTime_Size_32;
				optoskySpec->specInfo.attributes.integral_unit = IntegralTime_Unit_us;
				optoskySpec->specInfo.attributes.checkSum_type = Without_CheckBit;
			}
		}
		else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP3", 4)) {
			if (!strncmp(optoskySpec->specInfo.dev_model, "ATP3030", 7)) {
				optoskySpec->specInfo.attributes.pixel_number = 2048;
			}
			else {
				optoskySpec->specInfo.attributes.pixel_number = 4096;
			}
		}
		else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP4", 4)) {
			optoskySpec->specInfo.attributes.pixel_number = 3648;
		}
		else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP5", 4)) {
			if (!strncmp(optoskySpec->specInfo.dev_model, "ATP5000", 7) || \
				!strncmp(optoskySpec->specInfo.dev_model, "ATP5020", 7) || \
				!strncmp(optoskySpec->specInfo.dev_model, "ATP5001", 7) || \
				!strncmp(optoskySpec->specInfo.dev_model, "ATP5100", 7)) {
				optoskySpec->specInfo.attributes.pixel_number = 2048;
			}
			else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP5111", 7) || \
				!strncmp(optoskySpec->specInfo.dev_model, "ATP5003", 7) || \
				!strncmp(optoskySpec->specInfo.dev_model, "ATP5520", 7)) {
				optoskySpec->specInfo.attributes.pixel_number = 2068;
			}
			else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP5105", 7)) {
				optoskySpec->specInfo.attributes.pixel_number = 3072;
			}
			else {
				optoskySpec->specInfo.attributes.pixel_number = 2048;
			}
		}
		else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP6", 4)) {
			optoskySpec->specInfo.attributes.pixel_number = 1024;
		}
		else if (!strncmp(optoskySpec->specInfo.dev_model, "ATP8", 4)) {
			if (!strncmp(optoskySpec->specInfo.dev_model, "ATP8600", 4)) {
				optoskySpec->specInfo.attributes.pixel_number = 256;
			}
			else {
				optoskySpec->specInfo.attributes.pixel_number = 512;
			}
		}
		else {
			optoskySpec->specInfo.attributes.pixel_number = 2048;
		}
	}

	SUPPORT_MANA_LOG("!!!!The spectrometer device infomation\n"
		"[%s(%d)]:\nintegral time size is 0x%x. integral time unit is 0x%x. checkbit type is 0x%x\n",
		optoskySpec->specInfo.dev_model, \
		optoskySpec->specInfo.attributes.pixel_number, \
		optoskySpec->specInfo.attributes.integral_size, \
		optoskySpec->specInfo.attributes.integral_unit, \
		optoskySpec->specInfo.attributes.checkSum_type);
}

INT_8S optosky_open_spectrometer(void)
{
	libusb_device **dev_list;
	libusb_device *dev_match = NULL;
	INT_8S index = 0;

	if (optosky_interface_manager_state != 0) {
		return (-1);
	}
	optosky_system_log_init();

	INT_8S cnt = libusb_get_device_list(NULL, &dev_list);
	if (cnt < 0) {
		SUPPORT_MANA_LOG("libusb_get_device_list Error[%d]", cnt);
		return (-3);
	}

	while ((dev_match = dev_list[index++]) != NULL) {
		struct libusb_device_descriptor desc;
		libusb_get_device_descriptor(dev_match, &desc);

		if (desc.idVendor != OPTOSKY_USB_VID || desc.idProduct != OPTOSKY_USB_PID) continue;

		SUPPORT_MANA_LOG("matched the usb device!");
		INT_8S ret = libusb_open(dev_match, &usb_handle);
		if (ret < 0) {
			SUPPORT_MANA_LOG("libusb_open Error[%d]!", ret);
			return (-4);
		}
		ret = libusb_claim_interface(usb_handle, 0);
		if (ret < 0) {
			ret = libusb_detach_kernel_driver(usb_handle, 0);
			if (ret < 0) {
				libusb_close(usb_handle);
				SUPPORT_MANA_LOG("libusb_detach_kernel_driver failed!");
				return (-5);
			}
			ret = libusb_claim_interface(usb_handle, 0);
			if (ret < 0) {
				libusb_close(usb_handle);
				SUPPORT_MANA_LOG("libusb_claim_interface failed!");
				return (-6);
			}
		}
		optoskySpec.usbHandler = usb_handle;
		break;

	}
	libusb_free_device_list(dev_list, 1);

	if (dev_match) {
		optoskySpec.isOpen = 1;
		optosky_interface_manager_state = 1;
		optosky_get_device_infomation(&optoskySpec);
		SUPPORT_MANA_LOG("Found the target device & open success!");
		return (0);
	}
	else {
		SUPPORT_MANA_LOG("Do not found the target device!");
		return (-7);
	}
}


/*----------------------------------------------------------------------------*/
bool openSpectraMeter()
{
	libusb_device **dev_list;
	libusb_device *dev_match = NULL;
	INT_8S index = 0;

	if (optosky_interface_manager_state != 0) {
		return true;
	}
	optosky_system_log_init();

	INT_8S cnt = libusb_get_device_list(NULL, &dev_list);
	if (cnt < 0) {
		SUPPORT_MANA_LOG("libusb_get_device_list Error[%d]", cnt);
		return false;
	}

	while ((dev_match = dev_list[index++]) != NULL) {
		struct libusb_device_descriptor desc;
		libusb_get_device_descriptor(dev_match, &desc);

		if (desc.idVendor != OPTOSKY_USB_VID || desc.idProduct != OPTOSKY_USB_PID) continue;

		SUPPORT_MANA_LOG("matched the usb device!");
		INT_8S ret = libusb_open(dev_match, &usb_handle);
		if (ret < 0) {
			SUPPORT_MANA_LOG("libusb_open Error[%d]!", ret);
			return false;
		}
		ret = libusb_claim_interface(usb_handle, 0);
		if (ret < 0) {
			ret = libusb_detach_kernel_driver(usb_handle, 0);
			if (ret < 0) {
				libusb_close(usb_handle);
				SUPPORT_MANA_LOG("libusb_detach_kernel_driver failed!");
				return false;
			}
			ret = libusb_claim_interface(usb_handle, 0);
			if (ret < 0) {
				libusb_close(usb_handle);
				SUPPORT_MANA_LOG("libusb_claim_interface failed!");
				return false;
			}
		}
		optoskySpec.usbHandler = usb_handle;
		break;

	}
	libusb_free_device_list(dev_list, 1);

	if (dev_match) {
		optoskySpec.isOpen = 1;
		optosky_interface_manager_state = 1;
		optosky_get_device_infomation(&optoskySpec);
		SUPPORT_MANA_LOG("Found the target device & open success!");
		return true;
	}
	else {
		SUPPORT_MANA_LOG("Do not found the target device!");
		return false;
	}
}

bool closeSpectraMeter()
{
	if (optosky_interface_manager_state != 0) {
		libusb_release_interface(usb_handle, 0);
		libusb_close(usb_handle);
		usb_handle = NULL;
		optosky_interface_manager_state = 0;
		SUPPORT_MANA_LOG("Close the usb device!");
		return true;
	}
	else {
		SUPPORT_MANA_LOG("Close usb device failed!");
		return false;
	}
}
/*----------------------------------------------------------------------------*/


INT_8S optosky_close_spectrometer(void)
{
	if (optosky_interface_manager_state != 0) {
		libusb_release_interface(usb_handle, 0);
		libusb_close(usb_handle);
		usb_handle = NULL;
		optosky_interface_manager_state = 0;
		SUPPORT_MANA_LOG("Close the usb device!");
		return 0;
	}
	else {
		SUPPORT_MANA_LOG("Close usb device failed!");
		return (-1);
	}
}

INT_8U *optosky_get_library_version(void)
{
	return OPTOSKY_LIB_VERION;
}

////////////////////// Multiple Spectrometer Device Function //////////////////////
INT_8U optosky_get_device_list(__Spectrometer_Handle *spec_handle)
{
	libusb_device **dev_list;
	libusb_device *dev_match = NULL;
	INT_8S index = 0;
	INT_8U device_cnt = 0;

	INT_8S cnt = libusb_get_device_list(NULL, &dev_list);
	if (cnt < 0) {
		SUPPORT_MANA_LOG("libusb_get_device_list Error[%d]", cnt);
		return (-3);
	}

	while ((dev_match = dev_list[index++]) != NULL) {
		struct libusb_device_descriptor desc;
		libusb_get_device_descriptor(dev_match, &desc);

		if (desc.idVendor != OPTOSKY_USB_VID || desc.idProduct != OPTOSKY_USB_PID)
			continue;

		SUPPORT_MANA_LOG("matched the usb device!");
		INT_8S ret = libusb_open(dev_match, &usb_handles[device_cnt]);
		if (ret < 0) {
			SUPPORT_MANA_LOG("libusb_open Error[%d]!", ret);
			return (-4);
		}
		INT_8S *usb_serial = malloc(CHR_MAX_SIZE);
		if (!usb_serial) {
			free(usb_serial);
			return (-9);
		}
		ret = libusb_get_string_descriptor_ascii(usb_handles[device_cnt], desc.iSerialNumber, usb_serial, CHR_MAX_SIZE);
		if (ret > 0) {
			memcpy(optoskySpecs[device_cnt].usb_serial, usb_serial, ret); 
			memcpy(spec_handle[device_cnt].sn, usb_serial, ret);
			libusb_close(usb_handles[device_cnt]);
			usb_handles[device_cnt] = NULL;
			device_cnt++;
		}

		free(usb_serial);
	}
	libusb_free_device_list(dev_list, 1);
	return device_cnt;
}

INT_8S optosky_open_specified_spectrometer(__Spectrometer_Handle spec_handle)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-2);
	}

	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL) {
		return (-3);
	}

	if (optoskySpec->isOpen == 0) {
		libusb_device **dev_list;
		libusb_device *dev_match = NULL;
		INT_8S index = 0;
		INT_8U device_cnt = 0;

		INT_8S cnt = libusb_get_device_list(NULL, &dev_list);
		if (cnt < 0) {
			SUPPORT_MANA_LOG("libusb_get_device_list Error[%d]", cnt);
			return (-5);
		}
		while ((dev_match = dev_list[index++]) != NULL) {
			struct libusb_device_descriptor desc;
			libusb_get_device_descriptor(dev_match, &desc);

			if (desc.idVendor != OPTOSKY_USB_VID || desc.idProduct != OPTOSKY_USB_PID)
				continue;

			INT_8S *usb_serial = malloc(CHR_MAX_SIZE);
			if (!usb_serial) {
				free(usb_serial);
				return (-9);
			}
			SUPPORT_MANA_LOG("matched the usb device!");
			INT_8S ret = libusb_open(dev_match, &usb_handles[device_cnt]);
			if (ret < 0) {
				free(usb_serial);
				SUPPORT_MANA_LOG("libusb_open Error[%d]!", ret);
				return (-6);
			}
			ret = libusb_get_string_descriptor_ascii(usb_handles[device_cnt], desc.iSerialNumber, usb_serial, CHR_MAX_SIZE);

			if (ret <= 0) {
				free(usb_serial);
				continue;
			}

			if (!strncmp(optoskySpec->usb_serial, usb_serial, 16)) {
				ret = libusb_claim_interface(usb_handles[device_cnt], 0);
				if (ret < 0) {
					ret = libusb_detach_kernel_driver(usb_handles[device_cnt], 0);
					if (ret < 0) {
						free(usb_serial);
						SUPPORT_MANA_LOG("libusb_detach_kernel_driver failed!");
						return (-7);
					}
					ret = libusb_claim_interface(usb_handles[device_cnt], 0);
					if (ret < 0) {
						free(usb_serial);
						SUPPORT_MANA_LOG("libusb_claim_interface failed!");
						return (-8);
					}
				}
				optoskySpec->usbHandler = usb_handles[device_cnt];
				optoskySpec->isOpen = 1;
				optosky_get_device_infomation(optoskySpec);
				list_add(&optoskySpec->node, &device_list);
				free(usb_serial);
				active_number++;
				break;
			}

		}
	}
	else {
		/* this device is already opened!! */
		return (-1);
	}
	return 0;
}

INT_8S optosky_close_specified_spectrometer(__Spectrometer_Handle spec_handle)
{
	if (strlen(spec_handle.sn) == 0) {
		return (-2);
	}
	__Optosky_Spec *optoskySpec = get_spec_control_by_spec_handle(spec_handle);
	if (optoskySpec == NULL) {
		return (-3);
	}
	if (optoskySpec->isOpen == 1) {
		/* close success! */
		optoskySpec->isOpen = 0;
		libusb_release_interface(optoskySpec->usbHandler, 0);
		libusb_close(optoskySpec->usbHandler);
		optoskySpec->usbHandler = NULL;
		list_del(&optoskySpec->node);
		active_number--;
		return 0;
	}
	else {
		/* this device do not opened! */
		return (-1);
	}
}

INT_8S optosky_open_all_spectrometer(__Spectrometer_Handle *spec_handle)
{
	libusb_device **dev_list;
	libusb_device *dev_match = NULL;
	INT_8S index = 0;
	INT_8U device_cnt = 0;

	INT_8S cnt = libusb_get_device_list(NULL, &dev_list);
	if (cnt < 0) {
		SUPPORT_MANA_LOG("libusb_get_device_list Error[%d]", cnt);
		return (-3);
	}

	while ((dev_match = dev_list[index++]) != NULL) {
		struct libusb_device_descriptor desc;
		libusb_get_device_descriptor(dev_match, &desc);

		if (desc.idVendor == OPTOSKY_USB_VID && desc.idProduct == OPTOSKY_USB_PID) {
			SUPPORT_MANA_LOG("matched the usb device!");
			INT_8S ret = libusb_open(dev_match, &usb_handles[device_cnt]);
			if (ret < 0) {
				SUPPORT_MANA_LOG("libusb_open Error[%d]!", ret);
				return (-4);
			}
			INT_8S *usb_serial = malloc(CHR_MAX_SIZE);
			if (!usb_serial) {
				free(usb_serial);
				return (-9);
			}
			ret = libusb_get_string_descriptor_ascii(usb_handles[device_cnt], desc.iSerialNumber, usb_serial, CHR_MAX_SIZE);
			if (ret > 0) {
				if (optoskySpecs[device_cnt].isOpen == 1) {
					optoskySpecs[device_cnt].isOpen = 0;
					libusb_close(optoskySpecs[device_cnt].usbHandler);
					optoskySpecs[device_cnt].usbHandler = NULL;
					list_del(&optoskySpecs[device_cnt].node);
					active_number--;
				}
				if (optoskySpecs[device_cnt].isOpen == 0) {
					ret = libusb_claim_interface(usb_handles[device_cnt], 0);
					if (ret < 0) {
						ret = libusb_detach_kernel_driver(usb_handles[device_cnt], 0);
						if (ret < 0) {
							free(usb_serial);
							SUPPORT_MANA_LOG("libusb_detach_kernel_driver failed!");
							return (-5);
						}
						ret = libusb_claim_interface(usb_handles[device_cnt], 0);
						if (ret < 0) {
							free(usb_serial);
							SUPPORT_MANA_LOG("libusb_claim_interface failed!");
							return (-6);
						}
					}
					optoskySpecs[device_cnt].isOpen = 1;
					memcpy(optoskySpecs[device_cnt].usb_serial, usb_serial, ret);
					memcpy(spec_handle[device_cnt].sn, usb_serial, ret);
					optoskySpecs[device_cnt].usbHandler = usb_handles[device_cnt];
					optosky_get_device_infomation(&optoskySpecs[device_cnt]);
					list_add(&optoskySpecs[device_cnt].node, &device_list);
					free(usb_serial);
#if 0
					printf("!!!!The spectrometer device infomation\n"
						"[%s(%d)]:\nintegral time size is %d. integral time unit is %d. checkbit type is %d\n",
						optoskySpecs[device_cnt].specInfo.dev_model, \
						optoskySpecs[device_cnt].specInfo.attributes.pixel_number, \
						optoskySpecs[device_cnt].specInfo.attributes.integral_size, \
						optoskySpecs[device_cnt].specInfo.attributes.integral_unit, \
						optoskySpecs[device_cnt].specInfo.attributes.checkSum_type);
#endif
					device_cnt++;
					active_number++;
				}
				else {
					continue;
				}
			}
		}
	}

	libusb_free_device_list(dev_list, 1);
	if (active_number == 0) {
		return (-7);
	}
	else {
		return active_number;
	}
}

INT_8S optosky_close_all_spectrometer(void)
{
	INT_8U index = 0;
	for (; index < SPEC_NUMBER_MAX; index++) {
		if (optoskySpecs[index].isOpen) {
			break;
		}
	}
	if (index == SPEC_NUMBER_MAX) {
		return (-1);
	}
	for (index = 0; index < SPEC_NUMBER_MAX; index++) {
		if (optoskySpecs[index].isOpen) {
			optoskySpecs[index].isOpen = 0;
			libusb_release_interface(optoskySpecs[index].usbHandler, 0);
			libusb_close(optoskySpecs[index].usbHandler);
			optoskySpecs[index].usbHandler = NULL;
			list_del(&optoskySpecs[index].node);
			active_number--;
		}
	}
	return 0;
}

INT_8S optosky_initialize(void) {
	INT_8S ret = libusb_init(NULL);
	return ret;
}

void optosky_release(void) {
	libusb_exit(NULL);
}
