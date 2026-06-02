#include <stdio.h>
#include <stdlib.h>

#include "OptoskySupport.h"

INT_8U *library_version;

void external_trigger_info(INT_16U count, INT_16U *spectrum)
{
	INT_16U index = 0;
	
	printf("Trigger times: %d\n", count);
//	for(; index<2048; index++) {
//		printf("[%d]\t%d\n", index, spectrum[index]);
//	}
}

void main_help(void)
{
	printf("\r\n=========================OPTOSKY Demo(%s)=======================\r\n"
			"0 : API Open spectrometer\n"
			"1 : API Close spectrometer\n"
			"2 : API Get vendor\n"
			"3 : API Get PN\n"
			"4 : API Get SN\n"
			"5 : API Get module version\n"
			"6 : API Get module production date\n"
			////////////////////////////////////
			"20: API Get current integral time\n"
			"21: API Set current integral time\n"
			"22: API Set the average number of acquisitions\n"
			"23: API Get the wavelength range of the spectrometer\n"
			"30: API Start dark current spectrum acquisition(Synchronous waiting)\n"
			"31: API Start spectrum acquisition(Synchronous waiting)\n"
			"32: API Start dark current spectrum acquisition(Asynchronous)\n"
			"33: API Start spectrum acquisition(Asynchronous)\n"
			"34: API Get spectrum data\n"
			//"35: API Spectrum data Handler\n"
			////////////////////////////////////
			"40: API Set external GPIO status\n"
			"41: API Set External trigger acquisition enable\n"
			"42: API Set External trigger acquisition disable\n"
			"100 : exit\n"
            "====================================================================\r\n"
			"Enter : ", library_version);
}

int main(int argc, char **argv)
{
	INT_32S input_opt = 0;

    library_version = optosky_get_library_version();
    while(1) {
		main_help();
		scanf("%d", &input_opt);
		if(input_opt == 100) {
			break;
		}
		switch(input_opt) {
		case 0:{
			printf("API Open spectrometer\r\n");
			INT_8S ret = optosky_open_spectrometer();
			if(ret == 0) {
				printf("Open spectrometer success!\n");
			}else {
				if(ret == -1) {
					printf("Spectrometer already opened!\n");
					break;
                }
				printf("Open spectrometer failed!\n");
			}
        }break;
		case 1:{
			printf("API Close spectrometer\r\n");
			INT_8S ret = optosky_close_spectrometer();
			if(ret == 0) {
				printf("Close spectrometer success!\n");				
			}else {
				printf("Close spectrometer failed!\n");
			}
        }break;
		case 2:{
			printf("API Get vendor\r\n");
			INT_8S vendor_info[10] = {0};
			INT_8S ret = optosky_get_vendor(vendor_info, 10);
			if(ret < 0) {
				printf("Get vendor failed!\n");
			}else { 
				printf("Vendor : %s\n", vendor_info);
			}
	    }break;
		case 3:{
			printf("API Get PN number\r\n");
			INT_8S pn_info[10] = {0};
			INT_8S ret = optosky_get_PN(pn_info, 10);
			if(ret < 0) {
				printf("Get PN number failed!\n");
			}else {
				printf("PN : %s\n", pn_info);
			}
		}break;
		case 4:{
			printf("API Get SN number\r\n");
			INT_8S sn_info[10] = {0};
			INT_8S ret = optosky_get_SN(sn_info, 10);
			if(ret < 0) {
				printf("Get SN number failed!\n");
			}else {
				printf("SN : %s\n", sn_info);
			}
		}break;
		case 5:{
			printf("API Get module version\r\n");
			INT_8S version[10] = {0};
			INT_8S ret = optosky_get_version(version, 10);
			if(ret < 0) {
				printf("Get module version failed!\n");
			}else {
				printf("Version : %s\n", version);
			}
		}break;
		case 6:{
			printf("API Get module production date\r\n");
			INT_8S date[10] = {0};
			INT_8S ret = optosky_get_production_date(date, 10);
			if(ret < 0) {
				printf("Get module production date failed!\n");
			}else {
				printf("Production date : %s\n", date);
			}
		}break;
		case 20:{
			printf("API Get current integral time\r\n");
			INT_32U time = 0;
			INT_8S ret = optosky_get_integral_time(&time);
			if(ret ==  0) {
				printf("Current integral time : %d %s\n", time, \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? "ms" : "us");
			}else {
				printf("Get current integral time failed!\n");				
			}
		}break;
		case 21:{
			printf("API Set integral time:\r\n");
			printf("please input integral time(%s) : ", \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? \
                    "ms" : "us");
			scanf("%d", &input_opt);
			INT_8S ret = optosky_set_integral_time(input_opt);
			if(ret == 0) {
				printf("Set integral time success!\n");
			}else {
				printf("Set integral time failed!\n");				
			}
		}break;
		case 22:{
			printf("API Set the average number of acquisitions\r\n");
			printf("Please input the average number of times:");
            INT_32U scan_time = 0;
			scanf("%d", &scan_time);
			INT_8S ret = optosky_set_average(scan_time);
			if(ret < 0) {
				printf("Set average number of acquisitions failed!\r\n");
			}else {
				printf("Set average number of acquisitions success!\r\n");				
			}
		}break;
		case 23:{
			printf("API Get the wavelength range of the spectrometer\r\n");
			FLOAT wavelength[5000] = {0};
			INT_16S ret = optosky_get_wavelength_of_the_spec(wavelength, 2048);
			if(ret > 0) {
				INT_16U index = 0;
				printf("Pixel\tWavelength\n");
				for(; index<ret; index++) {
					printf("[%d]\t%f\n", index, wavelength[index]);
				}
			}else {
				printf("Get the wavelength range of the spectrometer failed!\n");
			}
		}break;
		case 30:{
			printf("API Start dark current spectrum acquisition(Synchronous waiting)\r\n");
			INT_32U integrationTime = 10;
			INT_16U spectrum[4096] = {0};
            printf("please input integral time(%s) : ", \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? \
                    "ms" : "us");
            scanf("%d", &integrationTime);
            INT_16S ret = optosky_acquisition_dark_sync(integrationTime, spectrum);
			if(ret > 0) {
                if(ret == 1) {
                    printf("The spectrometer is busy now!\n");
                    break;
                }
				INT_16U index = 0;
				printf("Pixel number : %d\nPixel\tCount\n", ret);
				for(; index<ret; index++) {
					printf("[%d]\t%d\n", index, spectrum[index]);
				}
			}else {
				printf("Get dark current spectrum error[%d]!\n", ret);
			}
		}break;
		case 31:{
			printf("API Start spectrum acquisition(Synchronous waiting)\r\n");
			INT_32U integrationTime = 10;
			INT_16U spectrum[8000] = {0};
            printf("please input integral time(%s) : ", \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? \
                    "ms" : "us");
            scanf("%d", &integrationTime);
			INT_16S ret = optosky_acquisition_spectrum_sync(integrationTime, spectrum);
			if(ret > 0) {
                if(ret == 1) {
                    printf("The spectrometer is busy now!\n");
                    break;
                }
                INT_16U index = 0;
				printf("Pixel number : %d\nPixel\tCount\n", ret);
                for(; index<ret; index++) {
					printf("[%d]\t%d\n", index, spectrum[index]);
				}
			}else {
				printf("Get spectrum error[%d]!\n", ret);
			}
		}break;
		case 32:{
			printf("API Start dark current spectrum acquisition(Asynchronous)\r\n");
			INT_32U integrationTime = 10;
            printf("please input integral time(%s) : ", \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? \
                    "ms" : "us");
            scanf("%d", &integrationTime);
			INT_8S ret = optosky_acquisition_dark_async(integrationTime);
			if(ret == 0) {
				printf("Start dark current spectrum(Asynchronous) success!\n");
			}else {
				printf("Start dark current spectrum(Asynchronous) error!\n");
			}
		}break;
		case 33:{
			printf("API Start spectrum acquisition(Asynchronous)\r\n");
			INT_32U integrationTime = 10;
            printf("please input integral time(%s) : ", \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? \
                    "ms" : "us");
            scanf("%d", &integrationTime);
			INT_8S ret = optosky_acquisition_spectrum_async(integrationTime);
			if(ret == 0) {
				printf("Start spectrum acquisition(Asynchronous) success!\n");
			}else {
				printf("Start spectrum acquisition(Asynchronous) error!\n");
			}
		}break;
		case 34:{
			printf("API Get spectrum data\r\n");
			INT_16U spectrum[8000] = {0};
			INT_16S ret = optosky_get_spectrum_data_async(spectrum);
			if(ret > 0) {
				INT_16U index = 0;
				printf("Pixel number : %d\nPixel\tCount\n", ret);
				for(; index<ret; index++) {
					printf("[%d]\t%d\n", index, spectrum[index]);
				}
			}else {
				printf("Get spectrum error!\n");
			}
		}break;
        case 35:
            break;
		case 40:{
			printf("API Set external GPIO status\r\n");
            EXT_GPIO_PIN pin; 
            EXT_GPIO_VALUE value;
            printf("please input pin number(0 ~ 11):");
            scanf("%d", &pin);
            printf("\nplease input pin value(0 or 1):");
            scanf("%d", &value);
			INT_8S ret = optosky_set_external_GPIO_value(pin, value);
			if(ret == 0) {
				printf("Set external GPIO%d status %d success!\n", pin, value);
			}else {
				printf("Set external GPIO%d status %d error!\n", pin, value);
			}
		}break;
		case 41:{
			printf("API Set External trigger acquisition enable\r\n");
            printf("please input integral time(%s) : ", \
                    optosky_get_integral_time_unit()==IntegralTime_Unit_ms? \
                    "ms" : "us");
			INT_32U integrationTime = 10;
            scanf("%d", &integrationTime);
			INT_8S ret = optosky_external_trigger_enable(integrationTime, external_trigger_info);
			if(ret == 0) {
				printf(" Enable external triggrt success!\n");
			}else {
				printf(" Enable external triggrt error!\n");
			}
		}break;
		case 42:{
			printf("API Set External trigger acquisition disable\r\n");
			INT_8S ret = optosky_external_trigger_disable();
			if(ret == 0) {
				printf(" Disable external triggrt success!\n");
			}else {
				printf(" Disable external triggrt error!\n");
			}
		}break;
		default:
			break;
		}
	}
	return 0;
}



