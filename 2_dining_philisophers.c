#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <semaphore.h>

#define PCOUNT   5       /* No of philosophers/spoons */
#define forever  for(;;) /* Infinite loop */

sem_t semaphore [PCOUNT];                               // One semaphore for each spoon 
int   sleep_time[PCOUNT] = {1000, 200, 500, 750, 300 }; // Time each philosopher sleeps after eating in milliseconds
int   work_time [PCOUNT] = {500,  600, 600, 900, 200 }; // Time to eat the rice in millis
int   philisopher_id[]   = {0, 1, 2, 3, 4};

void *worker_thread(void *);

int main() {
	// Initialise all semaphores
	for (int i=0; i < PCOUNT; ++i) {
		sem_init(&semaphore[i], 0, 1);
	}
	pthread_t threads[PCOUNT];
	for(int i=0; i < PCOUNT;  ++i) {
		pthread_create(&threads[i], NULL, worker_thread, (void *) (philisopher_id + i));
	}
	for(int i=0; i< PCOUNT; ++i) {
		pthread_join(threads[i], NULL); // Actually, no thread will ever finish
	}
	return 0;
}

void swap(int *a, int *b) {
	*a ^= *b;
	*b ^= *a;
	*a ^= *b;
}

void *worker_thread(void *ptr) {
	int pid = *(int *)ptr; // Philosopher ID
	int leftSpoon = pid, rightSpoon = (pid + PCOUNT - 1) % PCOUNT;
	if (pid & 1) swap(&leftSpoon, &rightSpoon);
	forever {
		while ( sem_wait(&semaphore[leftSpoon]) == -1);
		while ( sem_wait(&semaphore[rightSpoon]) == -1); // In case of error, keep trying.
 
		// Do the work here..
		printf("Philisopher %d has begun eating with spoons %d, %d\n", pid, leftSpoon, rightSpoon);
		usleep(work_time[pid] * 1000);
		printf("Philisopher %d is done eating.\n", pid);

		while ( sem_post(&semaphore[rightSpoon]) == -1);
		while ( sem_post(&semaphore[leftSpoon]) == -1);

		usleep (sleep_time[pid] * 1000);
	}
	return NULL;
}
