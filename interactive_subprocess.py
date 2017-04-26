import os
import time
import select
import subprocess


class InteractiveSubrocess(object):
    def __init__(self, command):
        self._command = command
        self._proc = subprocess.Popen(self._command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)
        self._poller = select.epoll()
        self._poller.register(self._proc.stdout.fileno(), select.EPOLLIN)

    def waitForProcessToPrintString(self, string, timeout=5):
        print "Waiting for setup util to print '%s'" % (string,)
        output = ""
        timeOfStart = time.time()
        while not output.endswith(string):
            timeUntilExpiration = max(timeOfStart + timeout - time.time(), 0)
            flags = self._poller.poll(timeout=timeUntilExpiration)
            timeSinceStart = time.time() - timeOfStart
            hasTimeoutExpired = timeSinceStart > timeout
            if hasTimeoutExpired:
                message = ("Command %(command)s did not print '%(expected)s' on time (timeout: %(timeout)d)"
                           % dict(command=self._command, expected=string, timeout=timeout))
                raise Exception(message)
            if flags:
                output += self._proc.stdout.read(1)

    def write(self, string):
        self._proc.stdin.write(string)

    def waitToFinishSuccessfully(self):
        returncode = self._proc.wait()
        if returncode != os.EX_OK:
            msg = ("Command %(command)s failed (return code %(returncode)d. Output from setup: %(output)s"
                   % dict(command=self._command, returncode=returncode, output=self._proc.stdout.read()))
