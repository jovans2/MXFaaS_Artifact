#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/syscall.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

void rand_str(char *dest, size_t length) {
    char charset[] = "0123456789"
                     "abcdefghijklmnopqrstuvwxyz"
                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    *dest++ = ' ';
    *dest++ = '-';
    *dest++ = ' ';
    length -= 3;
    while (length-- > 0) {
        size_t index = (double) rand() / RAND_MAX * (sizeof charset - 1);
        *dest++ = charset[index];
    }
    *dest = '\n';
}

ssize_t recvfrom(int socket, void *restrict buffer, size_t length, int flags, struct sockaddr *restrict address, socklen_t *restrict address_len){
    ssize_t (*lrecvfrom)(int, void *restrict, size_t, int, struct sockaddr *restrict, socklen_t *restrict) = dlsym(RTLD_NEXT, "recvfrom");
    pid_t tid = syscall(SYS_gettid);
    pid_t pid = getpid();
    
    //inform runner that thread/process is blocked
    const char* str1 = "\nblocked - ";
    char *num;
    int fd;
    char * myfifo = "/tmp/blocked";
    mkfifo(myfifo, 0666);
    fd = open(myfifo, O_WRONLY);
    char mybuffer[(int)((ceil(log10(tid))+1)*sizeof(char)) + 20];
    asprintf(&num, "%d", tid);
    strcat(strcpy(mybuffer, str1), num);
    write(fd, mybuffer, (strlen(mybuffer) + 1));
    close(fd);

    ssize_t toReturnValue = lrecvfrom(socket, buffer, length, flags, address, address_len);
    //inform runner that it is unblocked
    
    fd = open(myfifo, O_WRONLY);
    const char* str1_new = "\nunblocked - ";
    char *num_new;
    char mybuffer_new[(int)((ceil(log10(tid))+1)*sizeof(char)) + 20];
    asprintf(&num_new, "%d", tid);
    strcat(strcpy(mybuffer_new, str1_new), num_new);
    char mybuffer_newest[(int)((ceil(log10(tid))+1)*sizeof(char)) + 100];
    char str2[] = { [10] = '\1' };
    rand_str(str2, sizeof(str2) - 1);
    strcat(strcpy(mybuffer_newest, mybuffer_new), str2);
    write(fd, mybuffer_newest, (strlen(mybuffer_newest) + 1));
    close(fd);

    //wait for confirmation
    int fd_conf;
    char arr1[3];
    char * myfifo_conf = "/tmp/myfifo";
    mkfifo(myfifo_conf, 0666);
    fd_conf = open(myfifo_conf, O_RDONLY);
    read(fd_conf, arr1, sizeof(arr1));
    printf("Read\n");
    close(fd_conf);
    printf("Send response\n");
    //send response
    return toReturnValue;
}