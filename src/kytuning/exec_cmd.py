#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import signal
import select
import traceback
from .logger import *



class CommandResult(object):
    def __init__(
            self,
            command="",
            stdout="",
            stderr="", tee="", exit_status=None, duration=0):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_status = exit_status
        self.duration = duration
        self.tee = tee
        self.stack = traceback.extract_stack()

    def __str__(self):
        return ("Command: %s\n"
                "Exit status: %s\n"
                "Duration: %s\n"
                "STDOUT: %s\n"
                "STDERR: %s\n"
                "STACK: %s\n"
                % (self.command, self.exit_status, self.duration,
                    self.stdout, self.stderr, self.stack)
                )


class ExecCmd(object):
    """
    run shell cmd:
        from exec_cmd import ExecCmd
        task = ExecCmd(command='ls', env='')
        result = task.run()
        print(result.stdout)
        print(result.stderr)
    """

    def __init__(self, command, timeout=None,  env=None, muted=False):
        self.command = command
        self.result = CommandResult(command)
        self.env = env
        self.timeout = timeout
        self.muted = muted


    def save_output(self, isstdout):


    def run(self):
        if self.sp is None:
            return self.result
        start = time.time()

        if self.timeout:
            time_left = self.stoptime - time.time()
        else:
            time_left = None
        status = None
        while not self.timeout or time_left > 0:
            readlist = [self.sp.stdout, self.sp.stderr]
            read_ready, _, _ = select.select(readlist, [], [], 1)
            
            if self.sp.stdout in read_ready:
                self.save_output(True)

            if self.sp.stderr in read_ready:
                self.save_output(False)

            status = self.sp.poll()
            if status is not None:
                self.result.exit_status = status
                break

            time_left = self.stoptime - time.time()

        for i in (True, False):
            self.save_output(i)

        self.result.duration = time.time() - start
        self.sp.stdout.close()
        self.sp.stderr.close()

        if self.result.exit_status > 0:
            logging.debug(self.result)
            logging.debug(traceback.extract_stack())

        return self.result

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        pass

    def get_pid(self):
        return self.sp.pid


if __name__ == '__main__':
    e = ExecCmd(command='ls /itmp', env = dict(os.environ, LC_ALL="C"))
    result = e.run();
    print(result)
