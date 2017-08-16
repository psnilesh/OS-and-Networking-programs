/**
 * @author Nilesh PS
 * Inter-Process communication using shared memory.
 * Producer Consumer problem implementation.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/wait.h>
#include <sys/types.h>

#define  forever      for (;;)
#define  CONSUMER_ID  1
#define  PRODUCER_ID  0
#define  BUFFER_SIZE  10


// Shared queue
struct pc_queue_t {
	int data[BUFFER_SIZE];
	int next_full, next_avail, count;
};

typedef struct pc_queue_t   pcq_t;

// Function declarations
void pc_queue_init(struct pc_queue_t *);
void init_shared_memory(void *);

/**
 * Child process is the consumer and parent, the producer.
 */
int main() {
	pid_t cproc_id;
	key_t shm_key = ftok("/tmp/foo", 'p');
	int   shm_id  = shmget(shm_key, sizeof(pcq_t), IPC_CREAT | 0755), nextItemId = 1;
	// Create an initialise a process shared mutex for synchronising control to shared 
	// buffer.
	pthread_mutex_t mutex;
	pthread_mutexattr_t attr;
	pthread_mutexattr_init(&attr);
	pthread_mutexattr_setpshared(&attr, 1);
	pthread_mutex_init(&mutex, &attr);
	pthread_mutexattr_destroy(&attr);
	// These pointers are to be used by producer process only!
	pc_queue_init(shmat(shm_id, NULL, 0));
	
	// And thou said, Let there be a process :-P
	cproc_id = fork();
	if (cproc_id == 0) {
		// Child process
		pcq_t *q = shmat(shm_id, NULL, 0);
		// Loop forever
		forever {
			// Acquire lock first
			pthread_mutex_lock(&mutex);
			// CRITICAL SECTION ENTER
			if (q->count) {
				printf("Consumed %d from index %d\n", q->data[q->next_full], q->next_full);
				q->next_full = (q->next_full + 1) % BUFFER_SIZE;
				q->count--;
			}
			// CRITICAL SECTION LEAVE
			pthread_mutex_unlock(&mutex);
			usleep(1000000 >> 1); // Sleep 500 millis
		}
	}
	else if (cproc_id > 0) {
		// Parent/ Producer Process
		pcq_t *q = shmat(shm_id, NULL, 0);
		forever {
			pthread_mutex_lock(&mutex);
			// CRITICAL SECTION ENTER
			if(q->count < BUFFER_SIZE) {
				q->data[q->next_avail] = nextItemId;
				printf("Produced item %d at index %d\n", nextItemId++, q->next_avail);
				q->next_avail = (q->next_avail + 1) % BUFFER_SIZE;
				q->count++;
			}
			// CRITICAL SECTION LEAVE
			pthread_mutex_unlock(&mutex);
			usleep(1000000 >> 2); // Sleep 1/4 a second.
		}
	}
	else {
		perror("fork");
	}
	return 0;
}


void pc_queue_init(struct pc_queue_t *q) {
	q->next_full = q->count = 0;
	q->next_avail = 0;
}

