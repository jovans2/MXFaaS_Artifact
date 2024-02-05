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
#include <arpa/inet.h>
#include <sys/time.h>
#include <stdlib.h>
#include <math.h>
#include <netdb.h>

#define PORT 3333

ssize_t recvfrom(int socketm, void *restrict buffer, size_t length, int flags, struct sockaddr *restrict address, socklen_t *restrict address_len){
    ssize_t (*lrecvfrom)(int, void *restrict, size_t, int, struct sockaddr *restrict, socklen_t *restrict) = dlsym(RTLD_NEXT, "recvfrom");
    pid_t tid = syscall(SYS_gettid);
    pid_t pid = getpid();
    int sock = 0, valread, client_fd;
    struct sockaddr_in serv_addr;
        
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\n Socket creation error \n");
        return -1;
    }

    bzero(&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    if (inet_pton(AF_INET, "0.0.0.0", &serv_addr.sin_addr)<= 0) {
        printf("\nInvalid address/ Address not supported \n");
        return -1;
    }

    if ((client_fd = connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr))) < 0) {
        printf("\nConnection Failed \n");
        return -1;
    }
    
    {
        char* num;
        const char* str1 = "\nblocked - ";
        char mybuffer[(int)((ceil(log10(tid))+1)*sizeof(char)) + 20];
        bzero(mybuffer, sizeof(mybuffer));
        asprintf(&num, "%d", tid);
        strcat(strcpy(mybuffer, str1), num);
        write(sock, mybuffer, sizeof(mybuffer));
    }
    ssize_t toReturnValue = lrecvfrom(socketm, buffer, length, flags, address, address_len);
    {   
        char* num;
        const char* str1 = "\nunblocked - ";
        char mybuffer[(int)((ceil(log10(tid))+1)*sizeof(char)) + 20];
        bzero(mybuffer, sizeof(mybuffer));
        asprintf(&num, "%d", tid);
        strcat(strcpy(mybuffer, str1), num);
        write(sock, mybuffer, sizeof(mybuffer));
        bzero(mybuffer, sizeof(mybuffer));
        valread = read(sock, mybuffer, sizeof(mybuffer));
        //close(client_fd);
    }
    return toReturnValue;
}
