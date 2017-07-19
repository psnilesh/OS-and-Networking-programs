/**
 * @author Nilesh PS
 *
 * This programs does the same thing the below given command does when run within the shell
 * $ cat /etc/passwd | awk -F : '{ print $1; }' | sort
 *
 * ie. It prints all the registered users in the current LINUX installation in SORTED order.
 */
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <error.h>

/**
 * Note : There are three processes, one for each program
 * 1) cat
 * 2) awk
 * 3) sort
 */

int main() {
	// Stores process ID of process running /bin/cat and /usr/bin/awk respectively.
	pid_t catPid, awkPid;
	// Two pipes for IPC between cat <-- Cat-pipe --> awk <-- Awk-Pipe --> sort
	int catPipe[2], awkPipe[2];
	if (pipe(catPipe) == -1) /* -1 means error */
		perror("pipe: catPipe");
	catPid = fork(); // Creates a new process
	if(catPid == 0) {
		// Code segment of the child process. Overwrite with a new /bin/cat image.
		close(catPipe[0]); // Close the reading end.
		// STDOUT of this process is redirected to the catPipe
		if (dup2(catPipe[1], STDOUT_FILENO) == -1)
			perror("dup2: catPipe[1], STDOUT");
		// Let the process begin :-)
		execl("/bin/cat", "cat", "/etc/passwd", (char *)NULL);
		// execl method should never return, print an error if it does.
		perror("cat");
	}
	else if (catPid > 0) { /* If fork() returns a +ve value, we are in the code segment of the parent process and */
        close(catPipe[1]); /* the return value is the process_id of the child process.                            */
		// Init a new pipe for awk-sort IPC.
		if (pipe(awkPipe) == -1 ) 
			perror("pipe: awkPipe");
		awkPid = fork();
		if (awkPid == 0) {
			// Run awk here..
			close(awkPipe[0]);
			// The STDIN of awk process is the output of process cat.
			if (dup2(catPipe[0], STDIN_FILENO) == -1)
				perror("dup2: catPipe[0], STDIN_FILENO");
			// STDOUt of awk process is redirected to awkPipe so that sort can read it.
			if (dup2(awkPipe[1], STDOUT_FILENO) == -1)
				perror("dup2: catPipe[1], STDOUT_FILENO");
			execl("/usr/bin/awk", "awk", "-F", ":", "{ print $1; }", "-", (char *) NULL);
			// Again, if execl returns, it's an error.
			perror("execl : awk");
		}
		else if(awkPid > 0) {
			// Run sort here..
			// Always close the unused end of the pipe, if not, it results in  undefind behaviour.
			close(awkPipe[1]);
			// STDIN of sort process is setup as the awkPipe. So in-effect, the output of awk is fed as the input to the sort process.
			// Hence, the result is achieved.
			if (dup2(awkPipe[0], STDIN_FILENO) == -1)
				perror("dup2: awkPipe[0], STDIN");
			execl("/usr/bin/sort", "sort");
			// Error
			perror("sort");
		}
		else {
			perror("fork2");
		}
	}
	else {
		perror("fork1");
	}
	return 0;
}