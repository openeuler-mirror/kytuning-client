"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl <liyulong@kylinos.cn>
 * Date: Thu Dec 14 10:15:51 2023 +0800
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import subprocess
import signal
import select
import traceback
import shlex
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
    Notice: if command contains ";" or "|", which means multiple command
    in oneline, please add shell=True explicitly.
    """

    def __init__(self, command, timeout=None,  env=None, muted=False, shell = False):
        self.command = command if shell else shlex.split(command)
        self.result = CommandResult(command)
        self.env = env
        self.timeout = timeout
        self.muted = muted
        self.shell = shell

        if not shell and ('|' in command or ';' in command):
            logging.error("Please add shell=True explicitly")
            self.sp = None
            return

        if self.timeout:
            self.stoptime = time.time() + timeout
        else:
            self.stoptime = sys.maxsize
        if timeout is not None and timeout <= 0:
            logging.error("Timeout reached not to spawn a task")
            self.sp = None
        else:
            self.sp = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=self.shell,
                preexec_fn=os.setpgid(0, 0),
                env=self.env)


    def save_output(self, isstdout):
        data = self.read_output(isstdout)
        if isstdout is True:
            self.result.stdout = self.result.stdout + data
        else:
            self.result.stderr = self.result.stderr + data
            self.result.stdout = self.result.stdout + data


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


    def read_output(self, isstdout):
        if isstdout:
            pipe = self.sp.stdout
        else:
            pipe = self.sp.stderr

        data = ""
        while select.select([pipe], [], [], 0)[0]:
            bufferline = pipe.readline()
            try:
                bufferline = bufferline.decode('utf-8')
            except Exception:
                bufferline = str(bufferline)
            if bufferline == "":
                break
            data += bufferline

        return data


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
