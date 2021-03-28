CC	=	gcc

CFLAGS  = -std=c99
INCPATH	= -I/usr/include/SDL2 -D_REENTRANT
LIBS	= -lncurses -ltinfo -lSDL2 -lpigpio


all:
	$(CC) joy_parse.c -o joy $(CFLAGS) $(INCPATH) $(LIBS)
run: all
	./joy