#include "optosky_systemLog_task.h"
#include "optosky_support_manager_task.h"

#define DEVICE_HOTPLUG_LOG(fmt, ...)	OPTOSKY_LOG_MSG_FILE("HOTPLUG", fmt, ##__VA_ARGS__)
#if 0
extern __Optosky_Spec optoskySpecs[SPEC_NUMBER_MAX];

int optosky_devices_hotplug_cb(libusb_context *ctx, libusb_device *device, libusb_hotplug_event event, void *user_data)
{
	if(event == LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED) {	/* Device connect... */
		DEVICE_HOTPLUG_LOG("A new device connect!");
		printf("A new device access!\n");
        /* FixMe. */
	}else if(event == LIBUSB_HOTPLUG_EVENT_DEVICE_LEFT) {	/* Device disconnected... */
        printf("device offline...\n");
		/* FixMe. */
	}

}
#endif


