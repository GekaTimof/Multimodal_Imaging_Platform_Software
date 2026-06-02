# C compiler options
CC = gcc
#CFLAGS	= -g -O2             
TARGET = OptoskyDemo
#LIBS = /usr/local/lib -lusb-1.0 -lm -lpthread -lOptoskySupport
LIBS = /usr/lib/aarch64-linux-gnu/libusb-1.0.a -lm -lpthread ./libOptoskySupport.so
INC	= /usr/include/libusb-1.0
EXCHAR = -fexec-charset=GB18030    

# Source files
SRCS = OptoskyDemo.c
 
# Object files
OBJS = $(SRCS:.c=.o)
 
# Make everything
all: $(TARGET)
	rm $(OBJS)
 
# Make the application
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(EXCHAR) -o $(TARGET) $(OBJS)  $(LIBS) 
 
# Dependencies
$(OBJS): %.o: %.c
	cd libOptoskySupport;make;cd -;
	$(CC) -c $(CFLAGS) $(EXCHAR) -o $@ $< -I$(INC)  
#
# Clean all object files...
#
 
clean:
	rm $(OBJS) $(TARGET) 
 

