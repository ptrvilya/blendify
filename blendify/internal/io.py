import os
import sys


class catch_stdout:
    """Stdout hook to ignore or reroute the blender output
    """
    def __init__(self, skip = False, logfile = None):
        """Creates a stdout hook object
        Args:
            skip: whether skip the hook pass the output to stdin
            logfile: filename to pass the output to (None to ignore the output completely)
        """
        self.skip = skip
        self.logfile_path = logfile if logfile is not None else os.devnull

    def __enter__(self):
        self.logfile = open(self.logfile_path, 'w')
        self.logfile_fd = self.logfile.fileno()
        self.stdout_fd = sys.stdout.fileno()
        self.saved_stdout_fd = os.dup(self.stdout_fd)
        sys.stdout.flush()
        os.close(self.stdout_fd)
        os.dup2(self.logfile_fd, self.stdout_fd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.close(self.stdout_fd)
        self.logfile.close()
        os.dup2(self.saved_stdout_fd, self.stdout_fd)
        os.close(self.saved_stdout_fd)
