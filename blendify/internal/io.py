import os
import sys


class catch_stdout:
    """Stdout hook to ignore or reroute the blender output
    """

    def __init__(self, skip=False, logfile=None):
        """Creates a stdout hook object
        Args:
            skip: whether to skip the hook and pass the output to stdout
            logfile: filename to pass the output to (None to ignore the output completely)
        """
        self.skip = skip
        self.logfile_path = logfile if logfile is not None else os.devnull

    def __enter__(self):
        if self.skip:
            return
        self.logfile = open(self.logfile_path, 'w')
        self.logfile_fd = self.logfile.fileno()
        self.stdout_fd = sys.stdout.fileno()
        self.saved_stdout_fd = os.dup(self.stdout_fd)
        sys.stdout.flush()
        os.close(self.stdout_fd)
        os.dup2(self.logfile_fd, self.stdout_fd)
        self.capture_internal_stdout = False
        if sys.stdout.fileno() != sys.__stdout__.fileno():
            self.capture_internal_stdout = True
            self.internal_stdout_fd = sys.__stdout__.fileno()
            self.saved_internal_stdout_fd = os.dup(self.internal_stdout_fd)
            sys.__stdout__.flush()
            os.close(self.internal_stdout_fd)
            os.dup2(self.logfile_fd, self.internal_stdout_fd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.skip:
            return
        os.close(self.stdout_fd)
        os.dup2(self.saved_stdout_fd, self.stdout_fd)
        os.close(self.saved_stdout_fd)
        if self.capture_internal_stdout:
            os.close(self.internal_stdout_fd)
            os.dup2(self.saved_internal_stdout_fd, self.internal_stdout_fd)
            os.close(self.saved_internal_stdout_fd)
        self.logfile.close()
