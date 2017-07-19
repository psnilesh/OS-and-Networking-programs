/**
 * @author Nilesh PS
 * @description
 * This program demonstrates the use of message queues for Inter-Process Communication.
 * Server program shown below will accept bounded-length messages from clients, 
 * assign a unique id to every message, log the message along with the id and return a response
 * to the client
 *
 * NOTE : This program use POSIX message queue. It's available only in linux kernel version >= 2.6
 *        Refer https://users.cs.cf.ac.uk/Dave.Marshall/C/node25.html for message queues using
 *        sys/msg.h.
 */
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
#include "__includes.h"

int main() {
	// Queue descriptor for our own queue and for client's queue
	mqd_t my_qd, client_qd;
	// Configure queue attributes
	struct mq_attr attr;
	attr.mq_flags   = 0;
	attr.mq_maxmsg  = MSG_MAX_COUNT;
	attr.mq_msgsize = sizeof(svreq);
	attr.mq_curmsgs = 0;
	// Create a new queue with name SERVER_QNAME
	mq_unlink(SERVER_QNAME);
	if ((my_qd = mq_open(SERVER_QNAME, O_CREAT | O_RDONLY, 0755, &attr)) == -1) {
		perror("mq_open");
		exit(EXIT_FAILURE);
	}
	// Request and Response objects
	svreq req;
	svres res;
	// Each message received has a unique hit_no.
	int hit_no = 1;
	while (true) {
		ssize_t len;
		// Receive a message, blocking call.
		while ((len = mq_receive(my_qd, (char *)&req, sizeof(req) + 1, 0)) == -1 || len != sizeof(svreq)) {
			perror("mq_receive");
		}
		// Open the client queue as write only
		req.qname[QNAME_MAX_SIZE] = req.buffer[MSG_MAX_SIZE] = '\0';
		if( (client_qd = mq_open(req.qname, O_WRONLY)) == -1)
			perror("mq_open:client");
		// Print the message received from client
		printf("%d. Received \' %s \' from %ld\n\n", hit_no, req.buffer, (long)req.pid);
		// Prepare the reply
		sprintf(res.buffer, "Your message id = %d", hit_no++);
		// Send the reply object
		if ( mq_send(client_qd, (char *)&res, sizeof(svres), 0) == -1)
			perror("mq_write");
		// Close the connection with the queue
		mq_close(client_qd);
	} 
	return 0;
}
