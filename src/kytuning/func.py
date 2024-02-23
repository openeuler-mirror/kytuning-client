#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os
from .exec_cmd import ExecCmd
from .config import KYConfig

class FUNC(object):
    def __init__(self):
        self.curenv = dict(os.environ, LC_ALL="C")
        self.funcId = {
            "FUNC_THREAD_NUM": self.func_thread_num,
            # iozone
            "FUNC_IOZONE_MEMSIZE": self.func_iozone_memsize,
            "FUNC_IOZONE_FILE": self.func_iozone_file,
            # jvm
            "FUNC_JVM_MXMEM": self.func_jvm_mxmem,
            # speccpu2006
            "FUNC_CPU2006_CONFIG": self.func_cpu2006_config,
            # speccpu2017
            "FUNC_CPU2017_CONFIG": self.func_cpu2017_config,
            }
        pass

    # FUNC_THREAD_NUM
    def func_thread_num(self, type: str = None):
        if type == 'single':
            return '1'
        elif type == 'multi':
            result = ExecCmd(command = 'lscpu  | grep "^CPU(s)" | awk -F: \'{print $2}\'', env = self.curenv).run()
            if result.exit_status == 0:
                return result.stdout.strip()
        return None

    def func_iozone_memsize(self, type):
        if type == 'half':
            return KYConfig().get(['iozone', 'memsize', 'half'])
        elif type == 'full':
            return KYConfig().get(['iozone', 'memsize', 'full'])
        elif type == 'double':
            return KYConfig().get(['iozone', 'memsize', 'double'])
        return None

    def func_iozone_file(self, type):
        if type is None or len(type) == 0:
            return KYConfig().get(['iozone', 'test_file'])
        return None

    def func_jvm_mxmem(self, type):
        return None

    def func_cpu2006_config(self, type):
        return None

    def func_cpu2017_config(self, type):
        return None

    def call(self, func: dict) -> dict:
        return rdict
