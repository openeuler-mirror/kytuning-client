"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl_kl <liyulong@kylinos.cn>
 * Date: Fri Feb 23 15:51:57 2024 +0800
"""
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
            result = ExecCmd(command = 'cat /proc/cpuinfo| grep "processor"| wc -l', env = self.curenv, shell=True).run()
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
        mxmem = KYConfig().get(['specjvm', 'mx_mem'])
        if mxmem is not None and len(mxmem) > 0:
            return mxmem
        ## 获取物理内存，单位为字节
        mxmem = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        ## 转化为MB
        mxmem = mxmem / (1024 ** 2) 
        ## 取2/3的内存
        mxmem = int(mxmem * 2 / 3)
        ## 转化成字符串
        if mxmem > 0:
            mxmem = str(mxmem) + 'm'
            return mxmem
        return None

    def func_cpu2006_config(self, type):
        arch_str = None
        arch = ExecCmd(command = 'uname -m', env = self.curenv).run()
        if arch.exit_status == 0:
            arch_str = arch.stdout.strip()
        if arch_str is None:
            return KYConfig().get(['speccpu2006', 'config_file'])
        else:
            cpu_config = None
            if arch_str == 'x86_64':
                cpu_config = KYConfig().get(['speccpu2006', 'config_file_x86'])
            elif arch_str == 'aarch64':
                cpu_config = KYConfig().get(['speccpu2006', 'config_file_arm'])
            if cpu_config is None or len(cpu_config) == 0:
                cpu_config = KYConfig().get(['speccpu2006', 'config_file'])
            if cpu_config is None or len(cpu_config) == 0:
                if arch_str == 'x86_64':
                    cpu_config = "cpu2006-x86-fix.cfg"
                elif arch_str == 'aarch64':
                    cpu_config = "cpu2006-arm64-fix.cfg"
            return cpu_config
        return None

    def func_cpu2017_config(self, type):
        arch_str = None
        arch = ExecCmd(command = 'uname -m', env = self.curenv).run()
        if arch.exit_status == 0:
            arch_str = arch.stdout.strip()
        if arch_str is None:
            return KYConfig().get(['speccpu2017', 'config_file'])
        else:
            cpu_config = None
            if arch_str == 'x86_64':
                cpu_config = KYConfig().get(['speccpu2017', 'config_file_x86'])
            elif arch_str == 'aarch64':
                cpu_config = KYConfig().get(['speccpu2017', 'config_file_arm'])
            if cpu_config is None or len(cpu_config) == 0:
                cpu_config = KYConfig().get(['speccpu2017', 'config_file'])
            if cpu_config is None or len(cpu_config) == 0:
                if arch_str == 'x86_64':
                    cpu_config = "cpu2017-x86-fix.cfg"
                elif arch_str == 'aarch64':
                    cpu_config = "cpu2017-arm64-fix.cfg"
            return cpu_config
        return None

    def call(self, func: dict) -> dict:
        rdict = {}
        for funcId, funcParam in func.items():
            if funcId in self.funcId.keys():
                ret = self.funcId[funcId](funcParam)
                rdict[funcId] = ret if ret else funcParam
            elif type(funcParam) == dict:
                rdict[funcId] = self.call(funcParam)
            else:
                rdict[funcId] = funcParam
        return rdict
