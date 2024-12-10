"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl <liyulong@kylinos.cn>
 * Date: Fri Dec 8 17:18:33 2023 +0800
"""
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
        self.depmgr = DependencyManager(self.scheme.get_rpm_list())
        self.report = Report(self.scheme.get_base_path())
        self.report.path_init()

    def _collect_env(self):
        try:
            data = EnvManager().collect()
            if data:
                self.report_data["env"] = data
        except:
            logging.warning('collect env failed.')
        pass

    def _install_dependent_rpms(self):
        try:
            self.depmgr.install()
        except:
            logging.warning('install dependent rpms failed.')
        pass

    def _remove_dependent_rpms(self):
        try:
            self.depmgr.uninstall()
        except:
            logging.warning('uninstall dependent rpms failed.')
        pass

    def _setup_config(self):
        try:
            for item in self.scheme.get_configs():
                item.setup()
        except:
            logging.warning('setup config failed.')
        pass

    def _reset_config(self):
        try:
            for item in self.scheme.get_configs():
                item.reset()
        except:
            logging.warning('reset config failed.')
        pass

    def _do_testcase(self, tcase):
        try:
            tcase.save_config()
            tcase.setup_config()
            tcase.build()
            maxit = self.scheme.get_maxiterations()
            for idx in range(maxit):
                logging.info("###### run testcase\'s {idx}/{maxit} times...".format(idx=idx+1, maxit=maxit))

                self.result = tcase.run()
                name = '{name}-{idx}'.format(name=tcase.name, idx=idx)
                tinf = self.scheme.to_data()
                tinf['testcase'] = tcase.to_data()
                data = self.find_and_read_result()
                self._export_result({"name": name, "tinf": tinf, "data": data})

                logging.info("###### run testcase\'s {idx}/{maxit} times done".format(idx=idx+1, maxit=maxit))
        except TestCaseError as e:
            logging.error(e)
            raise e
        except Exception as e:
            logging.error(e)
            raise e
        finally:
            tcase.clean()
            tcase.reset_config()
        pass

    def _check_testcase(self, tcase):
        return True

    def _do_testcases(self):
        total = len(self.scheme.testcases)
        for tidx in range(total):
            if self._check_testcase(self.scheme.testcases[tidx]) is not True:
                continue

            logging.info("#### run {tidx}/{total} testcase start".format(tidx=tidx+1, total=total))

            self._do_testcase(self.scheme.testcases[tidx])

            logging.info("#### run {tidx}/{total} testcase done".format(tidx=tidx+1, total=total))
        pass

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

    def _backup_result(self):
        for fold in self.result_folder:
            if not os.path.exists(fold):
                continue
            ret_raw_path = self.scheme.get_ret_raw_path()
            if ret_raw_path is not None and len(ret_raw_path) > 0:
                subproc_call("cp -rf {ret_folder}/* {ret_raw_path}/".format(ret_folder = fold, ret_raw_path = ret_raw_path))
            ret_path = self.scheme.get_ret_path()
            if ret_path is not None and len(ret_path) > 0:
                subproc_call("  rm -f {ret_path}/kytuning-result.xlsx;                       \
                                ret_file=\"$(find ../results/ -name '*.xlsx' | tail -n 1)\"; \
                                ".format(ret_path = ret_path))
            break
        pass

    def _export_result(self, data: dict):
        if self.report_data["env"] is not None and self.report_data["env_export"] == False:
            self.report.save_env_data(self.report_data["env"])
            self.report_data["env_export"] = True
        self.report.save_result(data["name"], data["tinf"], data["data"])
        self.report_data["datas"].append(data)

    def export(self, rpath = None):
        if rpath is not None:
            self.report.current_report_file = rpath
            if self.report_data["env"]:
                self.report.save_env_data(self.report_data["env"])
            if len(self.report_data["datas"]) > 0:
                for data in self.report_data["datas"]:
                    self.report.save_result(data["name"], data["tinf"], data["data"], only_xlsx = True)
        pass


class UnixbenchTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)
        self.result_folder = ["./results"]

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
            with open(save[0],'r') as fp:
                data = fp.read()
        return data


class StreamTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)
        self.result_folder = ["./results"]

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
            if item.startswith('Single') :
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
        self.result_folder = ["./results_last"]

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
        self.result_folder = ["./results"]

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
        # for item in os.listdir(save[0]):
        #     save = '{subdir}/{item}'.format(subdir=save[0], item=item)
        # if save:
        #     with open(save) as fp:
        #         data = fp.read()
        if save:
            with open(save[0],'r') as fp:
                data = fp.read()
        return data


class IoZoneTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)
        self.result_folder = ["./result"]

    def _check_testcase(self, tcase):
        for m in ['half', 'full', 'double']:
            if (tcase.test_cmd.find(m)) != -1:
                return False
        return True

    def find_and_read_result(self):
        data = None
        save = None
        tdir = './result'
        for item in os.listdir(tdir):
            if item.endswith('.log') is False:
                continue
            path = '{tdir}/{item}'.format(tdir=tdir, item=item)
            stat = os.stat('{tdir}/{item}'.format(tdir=tdir, item=item))
            if save is None:
                save = (path, stat)
            else:
                if stat.st_mtime >= save[1].st_mtime:
                    save = (path, stat)
        if save:
            with open(save[0],'r') as fp:
                data = fp.read()
        return data


class NetPerfTest(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)


class SpecJVM2008Test(BaseTest):
    def __init__(self, scheme=None):
        BaseTest.__init__(self, scheme)
        self.result_folder = ["./results"]

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
        self.result_folder = ["./result"]

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
        self.result_folder = ["./result"]

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
    __data = { 
                'unixbench' : UnixbenchTest, 
                'lmbench' : LmbenchTest,
                'fio' : FioTest,
                'iozone' : IoZoneTest,
                'stream' : StreamTest,
                'specjvm2008' : SpecJVM2008Test,
                'speccpu2006' : SpecCPU2006Test,
                'speccpu2017' : SpecCPU2017Test,
                'netperf'   : NetPerfTest,
            }

    def __init__(self):
        pass

    def get(self, path):
        with open(path, 'r') as f: 
            scheme = SchemeParser().parse(f) 
            scheme.prepare()

            key = scheme.get_test_type()
            if key:
                test = self.__data.get(key.lower())
                if test is not None:
                    return test(scheme)
            raise TestNotFound("no test named \'%s\'" % key)
        raise TestNotFound("file open failed \'%s\'" % path)

