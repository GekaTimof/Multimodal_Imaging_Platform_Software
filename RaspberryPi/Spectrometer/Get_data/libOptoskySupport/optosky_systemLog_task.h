#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <time.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <string.h>
#include <stdarg.h>
#include <dirent.h>
#include <pthread.h>

#define OPTOSKY_TMP_LOG_CONFIG_FILE_DIR	"/optosky/"
#define OPTOSKY_TMP_LOG_CONFIG_FILE		"/optosky/log.cfg"
#define OPTOSKY_TMP_LOG_FILE_DIR		"/optosky/log/"

#define OPTOSKY_TMP_MSG_LOG_MAX_SIZE	10240

void optosky_log_acquire_lock(void);
void optosky_log_release_lock(void);
void optosky_log_open(void);
void optosky_log_close(void);
void optosky_log_time(char* timemap, char timemapsize);
void optosky_log_format_msg(char *buf_ptr, int buf_size, char *fmt, ...);
void optosky_write_log_to_file(char *buf);

#define strlcpy(X,Y,Z) strcpy(X,Y)
#define strlcat(X,Y,Z) strcat(X,Y)

#define OPTOSKY_LOG_MSG_FILE(context, fmt, ...)	\
{ \
	char log_buf[OPTOSKY_TMP_MSG_LOG_MAX_SIZE];\
	char log_fmt[OPTOSKY_TMP_MSG_LOG_MAX_SIZE];\
	char time_fmt[10];\
	optosky_log_acquire_lock();\
	optosky_log_time(time_fmt, sizeof(time_fmt));\
	strlcpy(log_fmt, "%s [%s] : ", sizeof(log_fmt));\
	strlcat(log_fmt, fmt, sizeof(log_fmt));\
	optosky_log_format_msg(log_buf, OPTOSKY_TMP_MSG_LOG_MAX_SIZE, log_fmt, time_fmt, context, ##__VA_ARGS__);\
	optosky_write_log_to_file(log_buf);\
	optosky_log_release_lock();\
}

void optosky_system_log_init(void);

