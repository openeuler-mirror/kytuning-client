"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl <liyulong@kylinos.cn>
 * Date: Fri Dec 8 17:18:33 2023 +0800
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os
import yaml

conf_data = None
extra_data = {}

class KYConfig(object):
    conf_path = ["/etc/kytuning/kytuning.yaml", "./conf/kytuning.yaml"]

    def __init__(self):
        pass

    def load(self, cpath = None):
        """
        加载conf_path配置文件
        :param cpath: 额外的配置文件
        :return:
        """
        global conf_data
        if cpath is not None:
            self.conf_path.insert(0, cpath)
        for path in self.conf_path:
            if path is None:
                continue
            if os.path.exists(path):
                data = None
                with open(path, 'r') as f:
                    data = yaml.load(f, yaml.FullLoader)
                if data is None:
                    print("load config error")
                    continue
                conf_data = data
                break
        return self if conf_data is not None else None

    def add(self, conf: dict):
        """
        增加额外数据
        :param conf:字典类型的数据
        :return:
        """
        global extra_data
        extra_data.update(conf)

    def get(self, keys: list):
        """
        获取配置文件数据和额外数据
        :param keys:
        :return:
        """
        global extra_data, conf_data
        if keys is not None and len(keys) > 0:
            for tconf in [extra_data, conf_data]:
                for k in keys:
                    if k in tconf:
                        tconf = tconf[k]
                    else:
                        tconf = None
                        break
                if tconf is not None:
                    return tconf
        return None

    def get_main(self, key):
        return self.get(['main', key])

    @property
    def report_path(self):
        return self.get(['main', 'report_path'])

    @property
    def base_path(self):
        return self.get_main('base_path')

    @property
    def run_path(self):
        return self.get_main('run_path')

    @property
    def ret_path(self):
        return self.get_main('ret_path')

    @property
    def src_path(self):
        return self.get_main('src_path')
