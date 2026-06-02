#include "optosky_systemLog_task.h"

pthread_mutex_t optosky_log_lock_mutex;
static int optosky_log_config = 0;
static char OPTOSKY_TMP_LOG_FILE[64] = {0};
static FILE *optosky_log_fp = NULL;


void optosky_log_name(void)
{
	time_t timep;
	struct tm *p;
	
	time(&timep);
	p = localtime(&timep);
	snprintf(OPTOSKY_TMP_LOG_FILE, sizeof(OPTOSKY_TMP_LOG_FILE), "%s%04d%02d%02d", 
		    OPTOSKY_TMP_LOG_FILE_DIR, (1900+p->tm_year), (p->tm_mon+1), p->tm_mday);
	printf("log file name : %s\r\n", OPTOSKY_TMP_LOG_FILE);
}

void optosky_log_open(void)
{
	if(optosky_log_config == 1) {
		optosky_log_fp = fopen(OPTOSKY_TMP_LOG_FILE, "a+");
	}
}

void optosky_log_close(void)
{
	if(NULL != optosky_log_fp) {
		fclose(optosky_log_fp);
		optosky_log_fp = NULL;
	}
}

void optosky_log_acquire_lock(void)
{
	pthread_mutex_lock(&optosky_log_lock_mutex);
	optosky_log_open();
}

void optosky_log_release_lock(void)
{
	optosky_log_close();
	pthread_mutex_unlock(&optosky_log_lock_mutex);
}

void optosky_log_time(char* timemap, char timemapsize)
{
	time_t timep;
	struct tm *p;

	time(&timep);
	p = localtime(&timep);
	snprintf(timemap, timemapsize, "%02d:%02d:%02d", 
	         p->tm_hour, p->tm_min, p->tm_sec);
}

void optosky_log_format_msg(char *buf_ptr, int buf_size, char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    if (NULL != buf_ptr && buf_size > 0) {
      vsnprintf(buf_ptr, buf_size, fmt, ap);
    }
    va_end(ap);
}

void optosky_write_log_to_file(char *buf)
{        
    if(NULL != optosky_log_fp) {
       fprintf(optosky_log_fp, "%s", buf);
    }
}

void optosky_system_log_init(void)
{
    DIR *log_dir = NULL;
	FILE *cfg_fp = NULL;

	do{
		log_dir = opendir(OPTOSKY_TMP_LOG_CONFIG_FILE_DIR);
		if(NULL == log_dir) {
			if(-1 == mkdir(OPTOSKY_TMP_LOG_CONFIG_FILE_DIR, 0777)) {
				printf(" [%s] directory creation failed\r\n", OPTOSKY_TMP_LOG_CONFIG_FILE_DIR);
				break;
			}
			if(-1 == mkdir(OPTOSKY_TMP_LOG_FILE_DIR, 0777)) {
				printf(" [%s] directory creation failed\r\n", OPTOSKY_TMP_LOG_FILE_DIR);
				break;
			}
		}

		cfg_fp = fopen(OPTOSKY_TMP_LOG_CONFIG_FILE, "r");
		if(NULL == cfg_fp) {
			cfg_fp = fopen(OPTOSKY_TMP_LOG_CONFIG_FILE, "w+");
			if(NULL == cfg_fp) {
				printf("log.cfg file creation failed\r\n");
				break;
			}
			printf("log.cfg file dose not exit,so created and written log_status as CONSOLE\r\n");
			fprintf(cfg_fp, "%d", optosky_log_config);
		}

		fscanf(cfg_fp, "%d", &optosky_log_config);
		if(optosky_log_config == 1) {
			optosky_log_name();
			optosky_log_fp = fopen(OPTOSKY_TMP_LOG_FILE, "r");
			if(NULL != optosky_log_fp) {
				fclose(optosky_log_fp);
				optosky_log_fp = fopen(OPTOSKY_TMP_LOG_FILE, "a+");
				if(NULL != optosky_log_fp) {
					fprintf(optosky_log_fp, "\n\n\n");
					fclose(optosky_log_fp);
				}
				optosky_log_fp = NULL;
				break;
			}
			optosky_log_fp = fopen(OPTOSKY_TMP_LOG_FILE, "w+");
			if(NULL == optosky_log_fp) {
				printf("log file create failed\r\n");
				break;
			}
			printf("log file create success\r\n");
			fclose(optosky_log_fp);
		}
	}while(0);
	if(cfg_fp) {
		fclose(cfg_fp);
	}
	if(log_dir) {
		closedir(log_dir);
	}
}

