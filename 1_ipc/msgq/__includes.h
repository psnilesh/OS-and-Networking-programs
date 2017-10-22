/**
 * Necessary constants for IPC between a server and client using
 * message queue.
 */
#ifndef __INCLUDES__H
#define __INCLUDES__H

#include <unistd.h>
#include <sys/types.h>
#include <assert.h>

#define SERVER_QNAME    "/sample-server-queue"
#define QNAME_MAX_SIZE  32
#define MSG_MAX_SIZE    1024
#define MSG_MAX_COUNT   10

struct sv_request {
    pid_t pid;
    char  qname[QNAME_MAX_SIZE + 1];
    char  buffer[MSG_MAX_SIZE  + 1];
};

struct sv_response {
    char buffer[MSG_MAX_SIZE + 1];
};


typedef struct sv_request svreq;
typedef struct sv_response svres;


#endif