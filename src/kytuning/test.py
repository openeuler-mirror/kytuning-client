import os
import json
import logging
from .scheme import *
from .error import *
from .report import *


__all__ = [ 'TestFactory', 'UnixbenchTest', 'LmbenchTest', 'TestNotFound']

class TestNotFound(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class BaseTest(object):
    def __init__(self, scheme=None):
        self.scheme = scheme
        self.envmgr = None
        self.depmgr = None
        self.report = None
        self.result = None 

    def __str__(self):
        return self.project

    def prepare(self):
        self.envmgr = EnvManager()
        self.depmgr = DependencyManager(self.scheme.get_rpm_list())
        self.report = Report(self.scheme.get_base_path())
        self.report.path_init()


    def collect_env(self): 
        data = self.envmgr.collect()
        if data:
            self.report.save_env_data(data)

    def install_dependent_rpms(self):
        self.depmgr.install()

    def remove_dependent_rpms(self):
        self.depmgr.uninstall()

    def setup_config(self):
        for item in self.scheme.get_configs():
            item.setup()

    def reset_config(self):
        for item in self.scheme.get_configs():
            item.reset()

    def do_test(self):
        total = len(self.scheme.testcases)
        maxit = self.scheme.get_maxiterations()
        for tidx in range(total):
            t = self.scheme.testcases[tidx]
            for idx in range(maxit):
                logging.info("#### run {tidx}/{total} testcase\'s {idx}/{maxit} times...".format(
                    tidx=tidx+1, total=total, idx=idx+1, maxit=maxit))
                try:
                    t.save_config()
                    t.setup_config()
                    t.build()
                    self.result = t.run()
                    name = '{name}-{idx}'.format(name=t.name, idx=idx)
                    tinf = self.scheme.to_data()
                    tinf['testcase'] = t.to_data()
                    data = self.find_and_read_result()
                    self.report.save_result(name, tinf, data)
                except TestCaseError as e:
                    logging.error(e)
                    raise e
                except Exception as e:
                    logging.error(e)
                    raise e
                finally:
                    t.clean()
                    t.reset_config()
                    logging.info("#### run {tidx}/{total} testcase\'s {idx}/{maxit} times done".format(tidx=tidx+1, total=total, idx=idx+1, maxit=maxit))
    def find_and_read_result(self):
        if self.result:
            return self.result 
        return ''

    def export(self):
        self.report.export_result()

