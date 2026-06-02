BIN = libOptoskySupport.so
CC = gcc
CFLAGS = -shared -fPIC
LIBS = -lusb-1.0

INCS = -include ../OptoskySupport.h -I/usr/include/libusb-1.0	#头文件目录
SRCS := $(wildcard *.c)	#.c文件目录
COBJS := $(SRCS:.c=.o)

all:$(BIN)
	rm $(COBJS); mv $(BIN) ../

$(BIN):$(COBJS)
	$(CC) -o $(BIN) $(COBJS) $(LIBS) $(CFLAGS)

$(COBJS) : %.o: %.c
	$(CC) -c $< -o $@ $(INCS) $(CFLAGS)

clean:
	rm $(BIN) $(COBJS)
