#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <mqueue.h>
#include <sys/ipc.h>
#include <fcntl.h>
#include <error.h>
#include <stdbool.h>
#include <assert.h>
#include "__includes.h"

#define CLIENT_QNAME_PREFIX  "/sample-client-queue"

int main(int argc, char **argv) {
	/**
	 * Expects a string of length not greater than MSG_MAX_SIZE as
	 * a command line argument.
	 */
	assert( strlen(CLIENT_QNAME_PREFIX) < QNAME_MAX_SIZE - 5);
	int len;
	if (argc < 2) {
		fprintf(stderr, "No message!");
		exit(EXIT_FAILURE);
	}
	// Check the length of the argument
	len = strlen(argv[1]);
	if (len > MSG_MAX_SIZE) {
		fprintf(stderr, "Message size limit exceeded!");
		exit(EXIT_FAILURE);
	}
	// Queue descriptors for identifying server queue and our queue 
	// respectively.
	mqd_t qd_server, my_qd;
	// Connect with the server queue.
	qd_server = mq_open(SERVER_QNAME, O_WRONLY);
	// Failed to create a queue.
	if (qd_server == -1) {
		perror("mq_open:server");
		exit(EXIT_FAILURE);
	}
	// Create another message queue for receiving messages.
	struct mq_attr attr;
	attr.mq_flags   = 0;               // Set to O_NONBLOCK if asynchronous message passing is necessary.
	attr.mq_msgsize = sizeof(svres);   // Maximum size of message
	attr.mq_maxmsg  = MSG_MAX_COUNT;   // Maximum message that queue should hold at any instant.
	attr.mq_curmsgs = 0;               // Current no of mesages in queue.

	svreq req; // Request object
	svres res; // Response object
	// Since multiple instances(processes) of this program can exist at the same time, 
	// use process_id in the  queue name to ensure every process get a unique queue name. 
	sprintf(req.qname, "%s-%ld", CLIENT_QNAME_PREFIX, (long)getpid()); 
	req.pid = (long)getpid();
	// Create a queue for receiving messages
	if ((my_qd = mq_open(req.qname, O_CREAT | O_RDONLY, 0755, &attr)) == -1) {
		perror("mq_open:client");
		exit(EXIT_FAILURE);
	}
	strncpy(req.buffer, argv[1], MSG_MAX_SIZE);
	// Send the message
	if ( mq_send(qd_server, (char *)&req, sizeof(svreq), 0) == -1) {
		perror("mq_send");
		exit(EXIT_FAILURE);
	}
	// Wait for reply
	while ( (len = mq_receive(my_qd, (char *)&res, sizeof(res) + 1, 0)) == -1 || len != sizeof(res))
		perror("mq_receive");
	res.buffer[MSG_MAX_SIZE] = '\0';
	// Print the reply
	printf("Process id = %ld\n Reply :- %s\n\n", (long)getpid(), res.buffer);
	mq_close(qd_server);
	mq_close(my_qd);
	mq_unlink(req.qname);
	return 0;
}	