import os
import json
import logging
from .scheme import *
from .error import *
from .report import *
from .getenv import EnvManager 
from .dependency import DependencyManager 
from .scheme import subproc_call 
from .config import KYConfig

__all__ = [ 'TestFactory', 'UnixbenchTest', 'LmbenchTest', 'TestNotFound']

class TestNotFound(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class BaseTest(object):
    def __init__(self, scheme=None):
        self.config = KYConfig()
        self.scheme = scheme
        self.depmgr = None
        self.report = None
        self.result = None
        self.result_folder = [] # ["./results", "./result"]
        self.report_data = {"env": None, "env_export": False, "datas": []}

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
        self._collect_env()
        self._install_dependent_rpms()
        self._setup_config()
        try:
            self._do_testcases()
        except Exception as e:
            raise e
        finally:
            self._backup_result()
            self._reset_config()
            self._remove_dependent_rpms()
        pass

    def find_and_read_result(self):
        if self.result:
            return self.result 
        return ''

    def export(self):
        self.report.export_result()

class UnixbenchTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

    def find_and_read_result(self):
        data = None
        save = None
        tdir = './results'

        for item in os.listdir(tdir):
            if item.endswith('.html') or item.endswith('.log'):
                continue
            path = '{tdir}/{item}'.format(tdir=tdir, item=item)
            stat = os.stat('{tdir}/{item}'.format(tdir=tdir, item=item))
            if save is None:
                save = (path, stat)
            else:
                if stat.st_mtime >= save[1].st_mtime:
                    save = (path, stat)
        if save:
            with open(save[0]) as fp:
                data = fp.read()
        return data

class StreamTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

    def compare_and_return_newer(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        if a[1].st_mtime >= b[1].st_mtime:
            return a
        else:
            return b

    def find_and_read_result(self):
        s_save = None
        m_save = None
        tdir = './results'
        for item in os.listdir(tdir):
            path = '{tdir}/{item}'.format(tdir=tdir, item=item)
            stat = os.stat('{tdir}/{item}'.format(tdir=tdir, item=item))
            if item.startswith('Single'):
                s_save = self.compare_and_return_newer(s_save, (path, stat))
            else:
                m_save = self.compare_and_return_newer(s_save, (path, stat))

        data = { 'single': None, 'multiple': None } 
        if s_save:
            with open(s_save[0], 'r') as fp:
                data['single'] = fp.read()
        if m_save:
            with open(m_save[0], 'r') as fp:
                data['multiple'] = fp.read()
        return json.dumps(data)


class LmbenchTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

    def find_and_read_result(self):
        data = ''
        tres = './results/summary.out'

        if os.access(tres, os.R_OK):
            with open(tres, 'r') as fp:
                data = fp.read()
        return data


class FioTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)


class IoZoneTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

class NetPerfTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)


class SpecJVM2008Test(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

    def find_and_read_result(self):
        data = None
        save = None
        tdir = './results'

        for item in os.listdir(tdir):
            path = '{tdir}/{item}'.format(tdir=tdir, item=item)
            stat = os.stat('{tdir}/{item}'.format(tdir=tdir, item=item))
            if save is None:
                save = (path, stat)
            else:
                if stat.st_mtime >= save[1].st_mtime:
                    save = (path, stat)

        for item in os.listdir(save[0]):
            if item.endswith('.txt') is True:
                save = '{subdir}/{item}'.format(subdir=save[0], item=item)

        if save:
            with open(save) as fp:
                data = fp.read()
        return data


class SpecCPU2006Test(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

    def find_and_read_result(self):
        data = None
        save = None
        fileseq = None
        tdir = './result'

        for item in os.listdir(tdir):
            if item.endswith('.txt') is False:
                continue
            path = '{tdir}/{item}'.format(tdir=tdir, item=item)
            stat = os.stat('{tdir}/{item}'.format(tdir=tdir, item=item))
            if save is None:
                save = (path, stat)
                filenameinfo = item.split('.')
                fileseq = filenameinfo[1]
            else:
                if stat.st_mtime >= save[1].st_mtime:
                    save = (path, stat)
                    filenameinfo = item.split('.')
                    fileseq = filenameinfo[1]
        # if save:
        #     with open(save[0]) as fp:
        #         data = fp.read()
        data = { 'int': "", 'fp': "" } 
        if save:
            for item in os.listdir(tdir):
                if item.endswith(".txt") is False:
                    continue
                path = '{tdir}/{item}'.format(tdir=tdir,item=item)
                if item.startswith('CINT2006.'+str(fileseq)):
                    with open(path, 'r') as fp:
                        data['int'] = fp.read()
                if item.startswith('CFP2006.'+str(fileseq)):
                    with open(path, 'r') as fp:
                        data['fp'] = fp.read()
        return json.dumps(data)


class SpecCPU2017Test(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)

    def find_and_read_result(self):
        data = None
        save = None
        fileseq = None
        tdir = './result'
        for item in os.listdir(tdir):
            if item.endswith('.txt') is False:
                continue
            path = '{tdir}/{item}'.format(tdir=tdir, item=item)
            stat = os.stat('{tdir}/{item}'.format(tdir=tdir, item=item))
            if save is None:
                save = (path, stat)
                filenameinfo = item.split('.')
                fileseq = filenameinfo[1]
            else:
                if stat.st_mtime >= save[1].st_mtime:
                    save = (path, stat)
                    filenameinfo = item.split('.')
                    fileseq = filenameinfo[1]
        data = { 'intrate': "", 'intspeed': "",'fprate': "", 'fpspeed': "" }
        if save: 
            for item in os.listdir(tdir):
                if item.endswith(".txt") is False:
                    continue
                path = '{tdir}/{item}'.format(tdir=tdir,item=item)
                if item.startswith('CPU2017.'+str(fileseq)+'.intrate'):
                    with open(path, 'r') as fp:
                        data['intrate'] = fp.read()
                if item.startswith('CPU2017.'+str(fileseq)+'.intspeed'):
                    with open(path, 'r') as fp:
                        data['intspeed'] = fp.read()
                if item.startswith('CPU2017.'+str(fileseq)+'.fprate'):
                    with open(path, 'r') as fp:
                        data['fprate'] = fp.read()
                if item.startswith('CPU2017.'+str(fileseq)+'.fpspeed'):
                    with open(path, 'r') as fp:
                        data['fpspeed'] = fp.read()
        return json.dumps(data)
        # print(save)
        # if save:
        #     with open(save[0]) as fp:
        #         data = fp.read()
        #return data

class TestFactory(object):
    def __init__(self):
        self.data = { 
                'unixbench' : UnixbenchTest, 
                'lmbench' : LmbenchTest,
                'fio' : FioTest,
                'iozone' : IoZoneTest,
                'stream' : StreamTest,
                'specjvm2008' : SpecJVM2008Test,
                'speccpu2006' : SpecCPU2006Test,
                'speccpu2017' : SpecCPU2017Test,
                'netperf'   : NetPerfTest,}

    def get_test_class(self, key):
        if key:
            return self.data.get(key.lower())

    def get_test_object(self, key, scheme):
        cls = self.get_test_class(key)
        if cls is None:
            raise TestNotFound("no test named \'%s\'" % key)
        return cls(scheme)
