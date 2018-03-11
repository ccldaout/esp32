#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <termios.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>

#define STDIN 0
#define STDOUT 1
static int SOCK = -1;

static struct termios OriginalTermios;

static void quit(int sig)
{
    tcsetattr(STDIN, TCSAFLUSH, &OriginalTermios);
    (void)putchar('\n');
    exit(0);
}

static int setuptty(void)
{
    struct termios newterm;
    int dropflag;

    tcgetattr(STDIN, &OriginalTermios);

    (void)signal(SIGINT, quit);
    (void)signal(SIGHUP, quit);
    (void)signal(SIGTERM, quit);

    newterm = OriginalTermios;
    newterm.c_oflag = OPOST;
    newterm.c_iflag = IGNBRK;

    dropflag = ECHO|ECHOCTL|ECHOE|ECHOK|ECHOKE|ECHONL;
    dropflag |= ICANON|IEXTEN|ISIG|TOSTOP;
#if defined(ECHOPRT)
    dropflag |= ECHOPRT;
#endif
    newterm.c_lflag &= ~dropflag;

    return tcsetattr(STDIN, TCSAFLUSH, &newterm);
}

static int setuptcp(const char *host, int port)
{
    struct hostent *hostent;
    struct sockaddr_in inaddr;
    int sock;
    int val;

    if ((hostent = gethostbyname(host)) == 0)
	return -1;
    (void)memset(&inaddr, 0, sizeof(inaddr));
    (void)memcpy(&inaddr.sin_addr, hostent->h_addr, hostent->h_length);
    inaddr.sin_family = AF_INET;
    inaddr.sin_port = htons(port);
    //inaddr.sin_len = sizeof(inaddr);

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1)
	return -1;
    if (connect(sock, (struct sockaddr *)&inaddr, sizeof(inaddr)) == -1) {
	(void)close(sock);
	return -1;
    }
    val = 1;
    (void)setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, (char *)&val, sizeof(val));
    return sock;
}

static int sendall(int fd, const char *s, ssize_t n)
{
    const char *p = s;
    ssize_t z = n;
    while (z > 0) {
	if ((n = write(fd, p, z)) > 0) {
	    z -= n;
	    p += n;
	} else {
	    (void)printf("write failure: %d\n", fd);
	    return -1;
	}
    }
    return 0;
}

static void loop(void)
{
    fd_set mask;
    int in, out;
    char buffer[1024];
    ssize_t n;

    (void)signal(SIGPIPE, SIG_IGN);

    FD_ZERO(&mask);

    for (;;) {
	FD_SET(STDIN, &mask);
	FD_SET(SOCK, &mask);

	if (select(SOCK+1, &mask, 0, 0, 0) > 0) {
	    if (FD_ISSET(STDIN, &mask)) {
		in = STDIN;
		out = SOCK;
	    } else if (FD_ISSET(SOCK, &mask)) {
		in = SOCK;
		out = STDOUT;
	    }
	    if ((n = read(in, buffer, sizeof(buffer)-1)) > 0) {
		if (in == STDIN) {
		    buffer[n] = 0;
		    if (strchr(buffer, 29))
			return;
		}
		if (sendall(out, buffer, n) == -1)
		    return;
	    } else if (n == 0) {
		if (in == SOCK)
		    (void)printf("socket is closed by peer.\n");
		return;
	    } else {
		(void)printf("read failure: %d\n", in);
		return;
	    }
	}
    }
}

int main(int argc, char **argv)
{
    int sock;

    if (argc != 3) {
	(void)printf("Usage: pnet HOST PORT\n");
	exit(EXIT_FAILURE);
    }

    if ((SOCK = setuptcp(argv[1], strtol(argv[2], 0, 0))) == -1) {
	(void)printf("error: %s\n", strerror(errno));
	exit(EXIT_FAILURE);
    }

    if (setuptty() == -1) {
	(void)printf("error: %s\n", strerror(errno));
	exit(EXIT_FAILURE);
    }

    loop();
    quit(0);
    return 0;
}
