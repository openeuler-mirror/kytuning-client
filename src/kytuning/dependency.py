"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: wangqingzheng <wangqingzheng@kylinos.cn>
 * Date: Thu Dec 14 10:49:45 2023 +0800
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from .exec_cmd import ExecCmd

class DependencyError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class DependencyManager(object):
    env = dict(os.environ, LC_ALL="C")

    def __init__(self, rpmlist = []):
        self.rpmlist = rpmlist

        # already install, dont install again
        self.dont_install = []

        # not install, need  to install
        self.need_install = []

        # install success
        self.succ_install = []

        # install failed
        self.fail_install = []

        # uninstall success
        self.succ_uninstall = []

        # uninstall failed
        self.fail_uninstall = []

        if rpmlist == None:
            raise Exception("The len of rpmlist is 0")

        for rpm in rpmlist:
            installed = self.check_install(rpm)
            if installed == True:
                self.dont_install.append(rpm)
            else:
                self.need_install.append(rpm)


    def install_once(self, rpm=None):
        """
        安装软件
        :param rpm:
        :return:
        """
        if rpm == None:
            return False

        cmd = 'yum -y install ' + rpm
        result = ExecCmd(command = cmd, env = self.env).run()
        return 0 if result.exit_status == 0 else 1


    def install(self) -> list:
        """
        安装软件的列表
        :return:
        """
        for rpm in self.need_install:
           result =  self.install_once(rpm)
           if result == 0:
               self.succ_install.append(rpm)
           else:
               self.fail_install.append(rpm)

        if len(self.fail_install) > 0:
            # environment recovery
            self.uninstall_norecord()
            raise DependencyError("Dependency install failed:" + str(self.fail_install))

        return self.succ_install


    def uninstall_once(self, rpm):
        """
        卸载软件
        :param rpm:
        :return:
        """
        if rpm == None:
            return False

        cmd = 'yum -y remove ' + rpm
        result = ExecCmd(command = cmd, env = self.env).run()
        return 0 if result.exit_status == 0 else 1


    def uninstall_norecord(self):
        """
        卸载已经安装完成的软件
        :return:
        """
        for rpm in self.succ_install[::-1]:
            result = self.uninstall_once(rpm)
        

    def uninstall(self) :
        """
        卸载软件列表
        :return:
        """
        for rpm in self.succ_install[::-1]:
            result = self.uninstall_once(rpm)
            if result == 0:
                self.succ_uninstall.append(rpm)
            else:
                self.fail_uninstall.append(rpm)
                
        if len(self.fail_uninstall) > 0:
            raise DependencyError("Dependency uninstall failed:" + str(self.fail_uninstall))

        return self.succ_uninstall


    def check_install(self, rpm):
        """
        检测软件是否安装
        :param rpm:
        :return:
        """
        cmd = "rpm -qa  --queryformat '%{name}' " + rpm
        result = ExecCmd(command = cmd, env = self.env).run()

        '''
        If the result.stdout is not empty, 
        it means that the software package has been installed
        '''
        if result.exit_status == 0 and len(result.stdout) > 0:
            return True
        else:
            return False


if __name__ == "__main__":
    dep = DependencyManager(['ctags', 'yelp', 'nano', 'notexist'])
    try:
        install = dep.install()
    except Exception as e:
        print(e.args)

    uninstall = dep.uninstall()

    print("dont install: ", dep.dont_install)
    print("need install: ", dep.need_install)
    print("succ install: ", dep.succ_install)
    print("fail install: ", dep.fail_install)

    print("succ uninstall: ", dep.succ_uninstall)
    print("fail uninstall: ", dep.fail_uninstall)
