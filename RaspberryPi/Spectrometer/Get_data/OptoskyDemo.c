#include <stdio.h>
#include <stdlib.h>
#include "OptoskySupport.h"

void external_trigger_cb(INT_16U count, INT_16U *spectrum)
{
  INT_16U index = 0;

  printf("Trigger times: %d\n", count);
  /*
    for(; index<2048; index++) {
    printf("[%d]\t%d\n", index, spectrum[index]);
  }
    */
}

void sepcified_dev_external_trigger_cb(__Spectrometer_Handle spec_handle, INT_16U count, INT_16U *spectrum)
{
  INT_16U index = 0;

  printf("[%s]Trigger times: %d\n", spec_handle.sn, count);
  /*
    for(; index<2048; index++) {
      printf("[%d]\t%d\n", index, spectrum[index]);
    }
    */
}

void main_help(void)
{
  printf("\r\n=========================OPTOSKY Demo(%s)=======================\r\n"
         ////////////////// Signal Device Control Function //////////////////
         "0 : API Open spectrometer\n"
         "1 : API Close spectrometer\n"
         "2 : API Get vendor\n"
         "3 : API Get PN\n"
         "4 : API Get SN\n"
         "5 : API Get module version\n"
         "6 : API Get module production date\n"
         "20: API Get current integration time\n"
         "21: API Set current integration time\n"
         "22: API Set the average number of acquisitions\n"
         "23: API Get the wavelength range of the spectrometer\n"
         "24: API Set the automatic integration time function\n"
         "30: API Start dark current spectrum acquisition(Synchronous waiting)\n"
         "31: API Start spectrum acquisition(Synchronous waiting)\n"
         "32: API Start dark current spectrum acquisition(Asynchronous)\n"
         "33: API Start spectrum acquisition(Asynchronous)\n"
         "34: API Get spectrum data\n"
         "40: API Set external GPIO status\n"
         "41: API Set External trigger acquisition enable\n"
         "42: API Set External trigger acquisition disable\n"
         "43: Api Get TEC Temperature\n"
         "44: Api Get MCU's SoftVersion\n"
         ////////////////// Multiple Device Control Function //////////////////
         "50: API Get spectrometer list\n"
         "51: API Open specified spectromter\n"
         "52: API Close specified spectrometer\n"
         "53: API Open all spectrometers\n"
         "54: API Close all spectrometers\n"
         "55: API Get vendor of the specified spectrometer\n"
         "56: API Get PN of the specified spectrometer\n"
         "57: API Get SN of the specified spectrometer\n"
         "58: API Get module version of the specified spectrometer\n"
         "59: API Get module production date of the specified spectrometer\n"
         "70: API Get current integration time of the specified spectrometer\n"
         "71: API Set current integration time of the specified spectrometer\n"
         "72: API Set the average number of acquisitions of the specified spectrometer\n"
         "73: API Get the wavelength range of the specified spectrometer\n"
         "74: API Set the automatic integration time function of the specified spectrometer\n"
         "80: API Start dark current spectrum acquisition of the specified spectrometer(Synchronous waiting)\n"
         "81: API Start spectrum acquisition of the specified spectrometer(Synchronous waiting)\n"
         "82: API Start dark current spectrum acquisition of the specified spectrometer(Asynchronous)\n"
         "83: API Start spectrum acquisition of the specified spectrometer(Asynchronous)\n"
         "84: API Get spectrum data of the specified spectrometer\n"
         "90: API Set external GPIO status of the specified spectrometer\n"
         "91: API Set External trigger acquisition enable of the specified spectrometer\n"
         "92: API Set External trigger acquisition disable of the specified spectrometer\n"
         "93: Api Get TEC Temperature of the specified spectrometer\n"
         "94: Api Get MCU's SoftVersion of the specified spectrometer\n"
         /// Initialize and release
         "96: API Initialize this function must be called before calling any other function\n"
         "97: API Release should be called after closing all open devices and before your application terminates\n"

         "100 : exit\n"

         ///Adding instructions
         "101: API Open spectrometer-----openSpectraMeter\n"
         "102: API Close spectrometer-----closeSpectraMeter\n"
         "103: API Get the number of device pixels-----getPixelCount\n"
         "104: API Get current integral time-----getActualIntegrationTime\n"
         "105: API Set integral time-----setIntegrationTime:\n"
         "106: API Set the average number of acquisitions-----setAverage\n"
         "107: API Get the nonlinearity coefficients of the spectrometer\n"
         "108: API Get the shape coefficients of the spectrometer\n"
         "109: API Get the dark coefficients of the spectrometer\n"
         "110: API Start spectrum acquisition(Synchronous waiting), and process the original data\n"
         "====================================================================\r\n"
         "Enter : ", optosky_get_library_version());
}

__Spectrometer_Handle spec_handle[10];  /* multiple spectrometer device control handle */

int main(int argc, char **argv)
{
  INT_32S input_opt = 0;

  while(1) {
    main_help();
    
    scanf("%d", &input_opt);
    if(input_opt == 100) {
      break;
    }
    switch(input_opt) {
      case 11:{
        int fps = 0;
        printf("API Test the spectrometer speed\r\n");
        printf("please input integral time(%s) : ", \
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &input_opt);
        fps = optosky_speed_test_handler(input_opt);
        printf("FPS is %d\n", fps);
      }break;

      ////////////////////////// Signale Device Handler Function //////////////////////////
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
          INT_8S index = 0;

          printf("len:%d\r\n", ret);

          for (index = 0; index < ret; index++)
            {
              printf("%x,", pn_info[index]);
            }
          printf("\n");

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
                 optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
        }else {
          printf("Get current integral time failed!\n");
        }
      }break;
      case 21:{
        printf("API Set integral time:\r\n");
        printf("please input integral time(%s) : ", \
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
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
          printf("Set average number of acquisitions failed!\n");
        }else {
          printf("Set average number of acquisitions success!\n");				
        }
      }break;
      case 23:{
        printf("API Get the wavelength range of the spectrometer\r\n");
        FLOAT wavelength[2048] = {0};
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
      case 24:{
        printf("API Set the automatic integration time function\r\n");
        __Integral_Time_Mode mode;
        printf("0: Disable\n1: Enable\nplease input: ");
        scanf("%d", &input_opt);
        if(input_opt == 0) {
          mode = IntegralTime_Automatic_Disable;
        }else if(input_opt == 1) {
          mode = IntegralTime_Automatic_Enable;
        }else {
          printf("input error!\n");
        }
        if(optosky_integral_time_automatic(mode) == 0) {
          printf("Set the automatic integration time success!\n");
        }else {
          printf("Set the automatic integration time failed!\n");
        }
      }break;
      case 30:{
        printf("API Start dark current spectrum acquisition(Synchronous waiting)\r\n");
        INT_32U integrationTime = 10;
        INT_16U spectrum[4096] = {0};
        printf("please input integral time(%s) : ", \
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
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
        INT_16U spectrum[4096] = {0};
        printf("please input integral time(%s) : ", \
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms ? "ms" : "us");
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
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms ? "ms" : "us");
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
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms ? "ms" : "us");
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
        INT_16U spectrum[4096] = {0};
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
      case 40:{
        printf("API Set external GPIO status\r\n");
        EXT_GPIO_PIN pin; 
        EXT_GPIO_VALUE value;
        printf("please input pin number(0 ~ 11):");
        scanf("%d", (int *)&pin);
        printf("\nplease input pin value(0 or 1):");
        scanf("%d", (int *)&value);
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
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms ? "ms" : "us");
        INT_32U integrationTime = 10;
        scanf("%d", &integrationTime);
        INT_8S ret = optosky_external_trigger_enable(integrationTime, external_trigger_cb);
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
      case 43:{
        INT_8S temp_info[10] = {0};
        printf("API Get TEC Temperature\r\n");
        INT_8S ret = optosky_get_TEC_temperature(temp_info, 10);
        if(ret > 0) {
          printf("get TEC Temperature success! TEC temp is %s\n", temp_info);
        }else {
          printf("get TEC Temperature error!\n");
        }
      }break;
      case 44:{
        INT_8S temp_info[10] = {0};
        printf("API Get MCU's soft version\r\n");
        INT_8S ret = optosky_get_soft_version(temp_info, 10);
        if(ret > 0) {
          printf("get MCU's Soft version success! MCU's soft version is %s\n", temp_info);
        }else {
          printf("get Mcu's Soft version error!\n");
        }
      }break;
      ////////////////////////// Multiple Device Handler Function //////////////////////////
      case 50:{
        printf("API Get spectrometer list\r\n");
        INT_8S ret = optosky_get_device_list(spec_handle);
        if(ret > 0) {
          for(INT_8U index=0; index<ret; index++) {
            printf("[%d/%d] %s\n", index+1, ret, spec_handle[index].sn);
          }
        }else {
          printf("No spectrometer connection!\n");
        }
      }break;
      case 51:{
        printf("API Open specified spectromter\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S ret = optosky_open_specified_spectrometer(spec_handle[input_opt-1]);
        if(ret == 0) {
          printf("Open spectrometer success!\n");
        }else {
          if(ret == -1) {
            printf("Spectrometer already opened!\n");
          }else {
            printf("The spectrometer was not found![%d]\n", ret);
          }
        }
      }break;
      case 52:{
        printf("API Close specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S ret = optosky_close_specified_spectrometer(spec_handle[input_opt-1]);
        if(ret == 0) {
          printf("Close spectrometer success!\n");
        }else {
          if(ret == -1) {
            printf("The spectrometer is not opend!\n");
          }else {
            printf("The spectrometer was not found!\n");
          }
        }
      }break;
      case 53:{
        printf("API Open all spectrometers\r\n");
        INT_8S ret = optosky_open_all_spectrometer(spec_handle);
        if(ret > 0) {
          printf("Open all spectrometers success, number of device is %d!\n", ret);
        }else {
          printf("Open all spectrometers failed[%d]!\n", ret);
        }
      }break;
      case 54:{
        printf("API Close all spectrometers\r\n");
        INT_8S ret = optosky_close_all_spectrometer();
        if(ret == 0) {
          printf("Close all spectrometers success!\n");
        }else {
          printf("Close all spectrometers failed!\n");
        }
      }break;
      case 55:{
        printf("API Get vendor of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S vendor_info[10] = {0};
        INT_8S ret = optosky_get_specified_dev_vendor(spec_handle[input_opt-1], vendor_info, 10);
        if(ret < 0) {
          if(ret == -10) {
            printf("The spectrometer is not opened!\n");
          }else {
            printf("Get vendor failed![%d]\n", ret);
          }
        }else {
          printf("vendor : %s\n", vendor_info);
        }
      }break;
      case 56:{
        printf("API Get PN of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S pn_info[10] = {0};
        INT_8S ret = optosky_get_specified_dev_PN(spec_handle[input_opt-1], pn_info, 10);
        if(ret < 0) {
          if(ret == -10) {
            printf("The spectrometer is not opened!\n");
          }else {
            printf("Get PN number failed![%d]\n", ret);
          }
        }else {
          printf("PN : %s\n", pn_info);
        }
      }break;
      case 57:{
        printf("API Get SN of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S sn_info[10] = {0};
        INT_8S ret = optosky_get_specified_dev_SN(spec_handle[input_opt-1], sn_info, 10);
        if(ret < 0) {
          if(ret == -10) {
            printf("The spectrometer is not opened!\n");
          }else {
            printf("Get SN number failed![%d]\n", ret);
          }
        }else {
          printf("SN : %s\n", sn_info);
        }
      }break;
      case 58:{
        printf("API Get module version of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S version[10] = {0};
        INT_8S ret = optosky_get_specified_dev_version(spec_handle[input_opt-1], version, 10);
        if(ret < 0) {
          if(ret == -10) {
            printf("The spectrometer is not opened!\n");
          }else {
            printf("Get Version failed![%d]\n", ret);
          }
        }else {
          printf("Version : %s\n", version);
        }
      }break;
      case 59:{
        printf("API Get module production date of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S date[10] = {0};
        INT_8S ret = optosky_get_specified_dev_production_date(spec_handle[input_opt-1], date, 10);
        if(ret < 0) {
          if(ret == -10) {
            printf("The spectrometer is not opened!\n");
          }else {
            printf("Get date failed![%d]\n", ret);
          }
        }else {
          printf("date : %s\n", date);
        }
      }break;
      case 70:{
        printf("API Get current integral time of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_32U time = 0;
        INT_8S ret = optosky_get_specified_dev_integral_time(spec_handle[input_opt-1], &time);
        if(ret ==  0) {
          printf("Current integral time : %d %s\n", time, \
                 optosky_get_specified_dev_integral_time_unit(spec_handle[input_opt-1]) == IntegralTime_Unit_ms? "ms" : "us");
        }else {
          printf("Get current integral time failed!\n");
        }
      }break;
      case 71:{
        printf("API Set current integral time of the specified spectrometer\r\n");
        INT_32U time = 0;
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("please input integral time(%s) : ", \
               optosky_get_specified_dev_integral_time_unit(spec_handle[input_opt-1]) == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &time);
        INT_8S ret = optosky_set_specified_dev_integral_time(spec_handle[input_opt-1], time);
        if(ret ==  0) {
          printf("Set integral time success!\n");
        }else {
          printf("Set integral time failed!\n");  
        }
      }break;
      case 72:{
        printf("API Set the average number of acquisitions of the specified spectrometer\r\n");
        INT_32U scan_times = 0;
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("Please input the average number of times:");
        scanf("%d", &scan_times);
        INT_8S ret = optosky_set_specified_dev_average(spec_handle[input_opt-1], scan_times);
        if(ret < 0) {
          printf("Set average number of acquisitions failed!\r\n");
        }else {
          printf("Set average number of acquisitions success!\r\n");				
        }
      }break;
      case 73:{
        printf("API Get the wavelength range of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        FLOAT wavelength[2048] = {0};
        INT_16S ret = optosky_get_specified_dev_wavelength_of_the_spec(spec_handle[input_opt-1], wavelength, 2048);
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
      case 74:{
        printf("API Set the automatic integration time function of the specified spectrometer\r\n");
        __Integral_Time_Mode mode;
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("0: Disable\n1: Enable\nplease input: ");
        scanf("%d", (int *)&mode);
        INT_8S ret = optosky_specified_dev_integral_time_automatic(spec_handle[input_opt-1], mode);
        if(ret == 0) {
          printf("Set the automatic integration time function success!\n");
        }else {
          printf("Set the automatic integration time function failed!\n");
        }
      }break;
      case 80:{
        printf("API Start dark current spectrum acquisition of the specified spectrometer(Synchronous waiting)\r\n");
        INT_32U integrationTime = 10;
        INT_16U spectrum[4096] = {0};
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("please input integral time(%s) : ", \
               optosky_get_specified_dev_integral_time_unit(spec_handle[input_opt-1]) == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &integrationTime);
        INT_16S ret = optosky_specified_dev_acquisition_dark_sync(spec_handle[input_opt-1], integrationTime, spectrum);
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
      case 81:{
        printf("API Start spectrum acquisition of the specified spectrometer(Synchronous waiting)\r\n");
        INT_32U integrationTime = 10;
        INT_16U spectrum[4096] = {0};
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("please input integral time(%s) : ", \
               optosky_get_specified_dev_integral_time_unit(spec_handle[input_opt-1]) == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &integrationTime);
        INT_16S ret = optosky_specified_dev_acquisition_spectrum_sync(spec_handle[input_opt-1], integrationTime, spectrum);
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
      case 82:{
        printf("API Start dark current spectrum acquisition of the specified spectrometer(Asynchronous)\r\n");
        INT_32U integrationTime = 10;
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("please input integral time(%s) : ", \
               optosky_get_specified_dev_integral_time_unit(spec_handle[input_opt-1]) == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &integrationTime);
        INT_8S ret = optosky_specified_dev_acquisition_dark_async(spec_handle[input_opt-1], integrationTime);
        if(ret == 0) {
          printf("Start dark current spectrum(Asynchronous) success!\n");
        }else {
printf("Start dark current spectrum(Asynchronous) error!\n");
        }
      }break;
case 83:{
  printf("API Start spectrum acquisition of the specified spectrometer(Asynchronous)\r\n");
  INT_32U integrationTime = 10;
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("please input integral time(%s) : ", \
               optosky_get_specified_dev_integral_time_unit(spec_handle[input_opt-1]) == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &integrationTime);
        INT_8S ret = optosky_specified_dev_acquisition_spectrum_async(spec_handle[input_opt-1], integrationTime);
        if(ret == 0) {
          printf("Start spectrum acquisition(Asynchronous) success!\n");
}else {
printf("Start spectrum acquisition(Asynchronous) error!\n");
        }
}break;
case 84:{
  printf("API Get spectrum data of the specified spectrometer\r\n");
  INT_16U spectrum[4096] = {0};
printf("please input the device number: ");
scanf("%d", &input_opt);
INT_16S ret = optosky_get_specified_dev_spectrum_data_async(spec_handle[input_opt-1], spectrum);
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
      case 90:{
        printf("API Set external GPIO status of the specified spectrometer\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        EXT_GPIO_PIN pin; 
        EXT_GPIO_VALUE value;
        printf("please input pin number(0 ~ 11):");
        scanf("%d", (int *)&pin);
        printf("\nplease input pin value(0 or 1):");
        scanf("%d", (int *)&value);
        INT_8S ret = optosky_set_specified_dev_external_GPIO_value(spec_handle[input_opt-1], pin, value);
        if(ret == 0) {
          printf("Set external GPIO%d status %d success!\n", pin, value);
        }else {
          printf("Set external GPIO%d status %d error!\n", pin, value);
        }
      }break;
      case 91:{
        printf("API Set External trigger acquisition enable\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        printf("please input integral time(%s) : ", \
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
        INT_32U integrationTime = 10;
        scanf("%d", &integrationTime);
        INT_8S ret = optosky_specified_dev_external_trigger_enable(spec_handle[input_opt-1], \
                                                                   integrationTime, \
                                                                   sepcified_dev_external_trigger_cb);
        if(ret == 0) {
          printf(" Enable external triggrt success!\n");
        }else {
          printf(" Enable external triggrt error!\n");
        }
      }break;
      case 92:{
        printf("API Set External trigger acquisition disable\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S ret = optosky_specified_dev_external_trigger_disable(spec_handle[input_opt-1]);
        if(ret == 0) {
          printf(" Disable external triggrt success!\n");
        }else {
          printf(" Disable external triggrt error!\n");
        }
      }break;
      case 93:{
        INT_8S temp_info[10] = {0};
        printf("API Get TEC Temperature\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S ret = optosky_specified_dev_get_TEC_temperature(spec_handle[input_opt - 1], \
                                                               temp_info, 10);
        if(ret > 0) {
          printf("get TEC Temperature success! TEC temp is %s\n", temp_info);
        }else {
          printf("get TEC Temperature error!\n");
        }
        printf("TEC temperatuer:%s.\n", temp_info);
      }break;
      case 94:{
        INT_8S temp_info[10] = {0};
        printf("API Get MCU's soft version\r\n");
        printf("please input the device number: ");
        scanf("%d", &input_opt);
        INT_8S ret = optosky_get_specified_soft_version(spec_handle[input_opt - 1], \
                                                               temp_info, 10);
        if(ret > 0) {
          printf("get MCU's soft version! MCU's soft version is %s\n", temp_info);
        }else {
printf("get MCU's soft version error!\n");
        }
printf("MCU's soft version:%s.\n", temp_info);
}break;
      case 96: {
        printf("API Initialize this function must be called before calling any other function\r\n");
        INT_8S ret = optosky_initialize();
        if (ret == 0) {
          printf(" API Initialize success!\n");
        }
      else {
          printf(" API Initialize error!\n");
        }
      }break;
      case 97: {
        printf("API Release should be called after closing all open devices and before your application terminates\r\n");

        optosky_release();

        printf(" Release success!\n");
      }break;

      case 101: {
        printf("API Open spectrometer\r\n");
        bool ret = openSpectraMeter();
        if(ret == true) {
          printf("Open spectrometer success!\n");
        }else {
          printf("Open spectrometer failed!\n");
        }
      }break;

      case 102: {
        printf("API Close spectrometer\r\n");
        bool ret = closeSpectraMeter();
        if(ret == true) {
          printf("Close spectrometer success!\n");
        }else {
          printf("Close spectrometer failed!\n");
        }
      }break;

      case 103: {
        printf("API Get the number of device pixels\n");
        int ret = getPixelCount();
        if(ret < 0)
          printf("Get pixel count failed!\n");
        else
          printf("The number of device pixels is %d\r\n",ret);
      }break;

      case 104: {
        printf("API Get current integral time\r\n");
        int time = 0;
        time = getActualIntegrationTime();
        if(time > 0) {
          printf("Current integral time : %d %s\n", time, \
                 optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
        }else {
          printf("Get current integral time failed!\n");
        }
      }break;

      case 105: {
        printf("API Set integral time:\r\n");
        printf("please input integral time(%s) : ", \
               optosky_get_integral_time_unit() == IntegralTime_Unit_ms? "ms" : "us");
        scanf("%d", &input_opt);
        bool ret = setIntegrationTime(input_opt);
        if(ret == true) {
          printf("Set integral time success!\n");
        }else {
          printf("Set integral time failed!\n");				
        }
      }break;

      case 106: {
        printf("API Set the average number of acquisitions\r\n");
        printf("Please input the average number of times:");
        int scan_time = 0;
        scanf("%d", &scan_time);
        bool ret = setAverage(scan_time);
        if(ret == false) {
          printf("Set average number of acquisitions failed!\n");
        }else {
          printf("Set average number of acquisitions success!\n");				
        }
      }break;

      case 107:{
        printf("API Get the nonlinearity coefficients of the spectrometer\r\n");
        FLOAT nlcoefficient[8] = {0};
        INT_16S ret = optosky_get_nonlinearity_coefficient(nlcoefficient);
        if(ret > 0){
          INT_16U index = 0;
          printf("Pixel\tNonlinearity coefficients\n");
          for(; index<ret; index++){
            printf("[%d]\t%.10E\n", index, nlcoefficient[index]);
          }
        }else{
          printf("Get the nonlinearity coefficients of the spectrometer failed!\n");
        }       
      }break;

      case 108:{
        printf("API Get the shape coefficients of the spectrometer\r\n");
        FLOAT spcoefficient[2048] = {0};
        INT_16S ret = optosky_get_shape_coefficient(spcoefficient);
        if(ret > 0){
          INT_16U index = 0;
          printf("Pixel\tShape coefficients\n");
          for(; index<ret; index++){
            printf("[%d]\t%f\n", index, spcoefficient[index]);
          }
        }else{
          printf("Get the shape coefficients of the spectrometer failed!\n");
        }       
      }break;

      case 109:{
        printf("API Get the dark coefficients of the spectrometer\r\n");
        s_DARK_FACTOR DarkBuf[2048] = {0};
        INT_16S ret = optosky_get_dark_coefficient(DarkBuf);
        if(ret > 0){
          INT_16U index = 0;
          printf("Pixel\tDark coefficients.k\tDark coefficients.b\n");
          for(; index<ret; index++){
            printf("[%d]\t%f\t%f\n", index, DarkBuf[index].k, DarkBuf[index].b);
          }
        }else{
          printf("Get the dark coefficients of the spectrometer failed!\n");
        }       
      }break;

      case 110:{
        printf("API Start spectrum acquisition(Synchronous waiting), and process the original data\r\n");
        s_DARK_FACTOR dkcoefficient[2048] = {0};
        FLOAT nlcoefficient[8] = {0};
        FLOAT spcoefficient[2048] = {0};
        INT_32U integrationTime = 10;
        INT_16U spectrum[4096] = {0};
        FLOAT spectrum_processed[4096] = {0};
        bool isDeductDark = false;
        bool isNonlinearCorrect = false;
        bool isShapeCalibration = false;

        INT_16S ret = optosky_get_dark_coefficient(dkcoefficient);
        if(ret < 0){
          printf("Get the dark coefficients of the spectrometer failed! \n");  
        }else{
          isDeductDark = true;
          ret = optosky_get_nonlinearity_coefficient(nlcoefficient);
          if(ret < 0){
            printf("Get the nonlinearity coefficients of the spectrometer failed! \n");  
          }else{
            isNonlinearCorrect = true;
            ret = optosky_get_shape_coefficient(spcoefficient);
            if(ret < 0){
              printf("Get the shape coefficients of the spectrometer failed! \n");
            }else{
              isShapeCalibration = true;
              printf("please input integral time(%s) : ", \
                optosky_get_integral_time_unit() == IntegralTime_Unit_ms ? "ms" : "us");
              scanf("%d", &integrationTime);
              ret = optosky_acquisition_spectrum_sync(integrationTime, spectrum);
              if(ret > 0) {
                if(ret == 1) {
                  printf("The spectrometer is busy now!\n");
                  break;
                }
                dataProcess(spectrum, spectrum_processed, ret, isDeductDark, isNonlinearCorrect, isShapeCalibration, dkcoefficient, nlcoefficient, spcoefficient,integrationTime);
                printf("Pixel number : %d\nPixel\tCount\n", ret);
                INT_16U index = 0;
                for(; index<ret; index++) {
                  printf("[%d]\t%f\n", index, spectrum_processed[index]);
                }
              }else {
                printf("Get spectrum error[%d]!\n", ret);
              }
            }
          }    
        }       
      }break;

      default:
        break;
}
}
  return 0;
}

