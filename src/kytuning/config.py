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
        global extra_data
        extra_data.update(conf)

    def get(self, keys: list):
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
