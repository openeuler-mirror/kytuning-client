import os
import yaml
import logging
import itertools
import subprocess
from subprocess import SubprocessError

from .logger import log_init
from .func import *

__doc__ = """
"""

__all__ = ['SchemeParser', 'Scheme', 'TestConfig', 'TestCase', 'SchemeParserError', 'SchemeError', 'TestCaseError']

class TestConfigError(Exception):
    def __init__(self, code, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.code = code

class TestCaseError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class SchemeError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class SchemeParserError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

def subproc_call(command, timeout=None, check=False, hide=False):
    return subprocess.run(command, shell=True,  
            stdout=None, stderr=None,
            encoding='utf-8', timeout=timeout, check=check)


class TestCmd(object):
    def __init__(self, cmd, exfmt = None):
        self._cmd = None
        self._cmd_str = None
        self._cmd_raw = None
        self.__set(cmd, exfmt)

    def __set(self, cmd, exfmt):
        if cmd is not None:
            if type(cmd) == dict:
                if "c_param" in cmd:
                    rdict = FUNC().call(cmd["c_param"])
                    if exfmt is not None:
                        rdict.update(exfmt)
                    self._cmd_str = cmd["command"].format(**rdict)
                else:
                    self._cmd_str = cmd["command"]
                if "pre_cmd" in cmd:
                    self._cmd_str = cmd["pre_cmd"].format(command = self._cmd_str)
                self._cmd_raw = cmd["command"]
            else:
                if exfmt is not None:
                    self._cmd_str = self._cmd_raw = cmd.format(**exfmt)
                else:
                    self._cmd_str = self._cmd_raw = cmd
            self._cmd = cmd
        pass

    @property
    def cmd(self):
        return self._cmd_str

    @property
    def raw(self):
        return self._cmd_raw


class TestConfig(object):
    def __init__(self, name, desc, get_cmd, set_cmd, value):
        self.name = name 
        self.desc = desc 
        self.get_cmd = get_cmd 
        self.set_cmd = set_cmd
        self.value = value
        self.setup_cmd = self.set_cmd.format(value=value)
        self.reset_cmd = None

    def save(self):
        if self.get_cmd:
            try:
                r = subproc_call(self.get_cmd, hide=True)
                if r.returncode:
                    raise TestConfigError(r.returncode)
                assert (r.stdout is not None and len(r.stdout) > 0)
                self.reset_cmd = self.set_cmd.format(value=r.stdout.replace('\n', ''))
            except SubprocessError as e:
                raise TestConfigError(-1)


    def setup(self):
        if self.setup_cmd:
            try:
                r = subproc_call(self.setup_cmd)
                if r.returncode:
                    raise TestConfigError(r.returncode)
            except SubprocessError as e:
                raise TestConfigError(-1)

    def reset(self):
        if self.reset_cmd: 
            try:
                r = subproc_call(self.reset_cmd)
                if r.returncode:
                    raise TestConfigError(r.returncode)
            except SubprocessError as e:
                raise TestConfigError(-1)

    def to_data(self):
        return { 'name' : self.name, 'desc' : self.desc, 
                'setup' : self.setup_cmd, 'reset': self.reset_cmd }

    def __str__(self):
        return "TestConfig: (name:%s,desc:%s,setup:%s,reset:%s)" % (self.name, self.desc, self.setup_cmd, self.reset_cmd)

class TestCase(object):
    def __init__(self, name, clean_cmd, build_cmd, test_cmd):
        self.name = name 
        self._test_cmd = TestCmd(test_cmd)
        self.build_cmd = build_cmd
        self.clean_cmd = clean_cmd
        self.configs = []

    @property
    def test_cmd(self):
        return self._test_cmd.cmd

    @property
    def test_cmd_raw(self):
        return self._test_cmd.raw

    def add_config(self, data):
        if isinstance(data, TestConfig):
            self.configs.append(data)

    def save_config(self):
        for item in self.configs:
            try:
                item.save()
                logging.info('testcase({name}->save({cmd})) done'.format(name=self.name, cmd=item.get_cmd))
            except TestConfigError as e:
                logging.error('testcase({name}->save({cmd})) error[{code}]'.format(name=self.name, cmd=item.get_cmd, code=e))
                raise TestCaseError('testcase({name}->save({cmd})) error[{code}]'.format(name=self.name, cmd=item.get_cmd, code=e))


    def setup_config(self):
        for item in self.configs:
            try:
                item.setup()
                logging.info("testcase({name})->setup({cmd}) done".format(
                    name=self.name, cmd=item.setup_cmd))
            except TestConfigError as e:
                logging.error("testcase({name})->setup({cmd}) error[{code}]".format(
                    name=self.name, cmd=item.setup_cmd, code=e.code))
                raise TestCaseError("testcase({name})->setup({cmd}) error[{code}]".format(
                    name=self.name, cmd=item.setup_cmd, code=e.code))

    def reset_config(self):
        for item in self.configs:
            try:
                item.reset()
                logging.info("testcase({name})->reset({cmd}) done".format(
                    name=self.name, cmd=item.reset_cmd))
            except TestConfigError as e:
                logging.error("testcase({name})->reset({cmd}) error[{code}]".format(
                    name=self.name, cmd=item.reset_cmd, code=e.code))
                raise TestCaseError("testcase({name})->reset({cmd}) error[{code}]".format(
                    name=self.name, cmd=item.reset_cmd, code=e.code))

    def build(self):
        if self.build_cmd and len(self.build_cmd) > 0:
            logging.info("testcase({name})->build({build_cmd}) ...".format(
                name=self.name, build_cmd=self.build_cmd))
            try:
                r = subproc_call(self.build_cmd)
                if r.returncode:
                    raise TestCaseError("testcase({name})->build({build_cmd}) error[{code}]".format(
                        name=self.name, build_cmd=self.build_cmd, code=r))
            except SubprocessError as e:
                raise TestCaseError("testcase({name})->build({build_cmd}) error[{code}]".format(
                    name=self.name, build_cmd=self.build_cmd, code=e))
            logging.info("testcase({name})->build({build_cmd}) done".format(
                name=self.name, build_cmd=self.build_cmd))

    def clean(self):
        if self.clean_cmd and len(self.clean_cmd) > 0:
            logging.info('testcase({name})->clean({clean_cmd}) ...'.format(
                name=self.name, clean_cmd=self.clean_cmd))
            try:
                r = subproc_call(self.clean_cmd)
                if r.returncode:
                    raise TestCaseError("testcase({name})->build({build_cmd}) error[{code}]".format(
                        name=self.name, build_cmd=self.build_cmd, code=r))
            except SubprocessError as e:
                raise TestCaseError("testcase({name})->build({build_cmd}) error[{code}]".format(
                    name=self.name, build_cmd=self.build_cmd, code=e))
            logging.info('testcase({name})->clean({clean_cmd}) done'.format(
                name=self.name, clean_cmd=self.clean_cmd))

    def run(self): 
        if self.test_cmd and len(self.test_cmd) > 0:
            try:
                logging.info("testcase({name})->run({test_cmd}) ...".format(name=self.name, test_cmd=self.test_cmd))
                r = subproc_call(self.test_cmd)
                if r.returncode:
                    if r.stdout:
                        logging.error(r.stderr)
                    if r.stderr:
                        logging.error(r.stderr)
                    raise TestCaseError("testcase({name})->run({test_cmd}) error {code}.".format(
                        name=self.name, test_cmd=self.test_cmd, code=r))
                logging.info("testcase({name})->run({test_cmd}) done".format(name=self.name, test_cmd=self.test_cmd))
                return r.stdout
            except SubprocessError as e:
                raise TestCaseError("testcase({name})->run({test_cmd}) error {code}.".format(
                    name=self.name, test_cmd=self.test_cmd, code=e))

    def __str__(self):
        data = "testcase(name:%s)\n" % self.name
        data += "\tclean    : %s\n" % self.clean_cmd
        data += "\tbuild    : %s\n" % self.build_cmd
        data += "\trun      : %s\n" % self.test_cmd
        for tc in self.configs:
            data += "\t%s\n" % str(tc)
        return data

    def to_data(self):
        data = { 'name' : self.name, 'build' : self.build_cmd, 'clean' : self.clean_cmd, 'run' : self.test_cmd_raw }
        configs = []
        for e in self.configs:
            configs.append(e.to_data())
        data['configs'] = configs
        return data


class Scheme(object):
    def __init__(self):
        self.project = ''                 # 项目名称 
        self.test_type = ''                   # 项目类型 
        self.base_path = ''                # 根路径或者基本路径
        self.run_path = ''
        self.ret_path = ''
        self.ret_raw_path = ''
        self.src_path = ''
        self.tool_tgz = ''
        self.tool_dir = ''
        self.tool_decompression = ''
        self.log_level = 'info'                # 日志级别
        self.log_file = 'kytuning.log'
        self.rpm_list = []
        self.configs = []
        self.maxiterations = 1
        self.testcases = []

    def to_data(self):
        data = { 'project': self.project, 'test_type' : self.test_type, 'rpm_list' : self.rpm_list }
        configs = []
        for item in self.configs:
            configs.append(item.to_data())
        data['configs'] = configs
        return data

    def prepare(self):
        for k, v in {"base_path": self.base_path, "run_path": self.run_path, "ret_raw_path": self.ret_raw_path, "src_path": self.src_path}.items():
            if len(v) == 0:
                continue
            if os.access(v, os.F_OK) is True:
                continue
            try:
                os.makedirs(v)
            except PermissionError as e: 
                raise SchemeError("mkdir({path_name}={base_path}) error: {desc}".format(path_name = k, base_path = v, desc = e))
            except FileNotFoundError as e:
                raise SchemeError("mkdir({path_name}={base_path}) error: {desc}".format(path_name = k, base_path = v, desc = e))

        log_init(self.log_file, self.log_level)

        if self.tool_dir:
            if not os.path.exists(self.tool_dir):
                if self.tool_decompression:
                    logging.info('exec({tool_dec}) ...'.format(tool_dec=self.tool_decompression))
                    try:
                        r = subproc_call(self.tool_decompression)
                        if r.returncode:
                            raise SchemeError("exec({tool_dec}) error {code}.".format(tool_dec=self.tool_decompression, code=r))
                        logging.info('exec({tool_dec}) done'.format(tool_dec=self.tool_decompression))
                    except SubprocessError as e:
                        raise SchemeError("exec({tool_dec}) error {code}.".format(tool_dec=self.tool_decompression, code=e))
            try:
                os.chdir(self.tool_dir)
                logging.info("chdir({tool_dir}) done".format( tool_dir=self.tool_dir))
            except FileNotFoundError as e:
                raise SchemeError("chdir({tdir}) error:{desc}".format(tdir=self.tool_dir, desc=e))

    def get_project(self):
        return self.project

    def get_test_type(self):
        return self.test_type

    def get_base_path(self):
        return self.base_path

    def get_run_path(self):
        return self.run_path

    def get_ret_path(self):
        return self.ret_path

    def get_ret_raw_path(self):
        return self.ret_raw_path

    def get_src_path(self):
        return self.src_path

    def get_tool_decompression(self):
        return self.tool_decompression 

    def get_tool_dir(self):
        return self.tool_dir

    def get_log_level(self):
        return self.log_level

    def get_log_file(self):
        return self.log_file

    def get_rpm_list(self):
        return self.rpm_list

    def get_configs(self):
        return self.configs

    def get_maxiterations(self):
        return self.maxiterations

    def get_testcases(self):
        return self.testcases

    def __str__(self):
        data = "Scheme({value})\n".format(value=self.project)
        data += "\ttest_type   : {value}\n".format(value=self.test_type)
        data += "\tbase_path   : {value}\n".format(value=self.base_path)
        data += "\tret_path    : {value}\n".format(value=self.ret_path)
        data += "\tsrc_path    : {value}\n".format(value=self.src_path)
        data += "\tlog_file    : {value}\n".format(value=self.log_file)
        data += "\tlog_level   : {value}\n".format(value=self.log_level) 
        data += "\ttool_tgz    : {value}\n".format(value=self.tool_tgz)
        data += "\ttool_dir    : {value}\n".format(value=self.tool_dir) 
        data += "\ttool_decompression   : {value}\n".format(value=self.tool_decompression)
        data += "\tmaxiterations        : {value}\n".format(value=self.maxiterations)
        data += "\trpm_list    : {rpm_list}\n".format(rpm_list=str(self.rpm_list))
        data += "configs:\n"
        for item in self.configs:
            data += ("\t" + str(item) + "\n")

        for testcase in self.testcases:
            data += str(testcase)
        return data


class SchemeParser(object):
    def __init__(self):
        self.config = KYConfig()
        pass

    def parse(self, stream): 
        try:
            data = yaml.load(stream, yaml.FullLoader) 
            if data is None:
                return None

            scheme = Scheme() 

            scheme.project = data.get('project')
            if scheme.project is None:
                raise SchemeParserError("missing 'project'")

            scheme.test_type = data.get('test_type')
            if scheme.test_type is None:
                raise SchemeParserError("missing 'test_type'")

            scheme.base_path = data.get('base_path')
            if scheme.base_path is None:
                if self.config.get(['main', 'base_path']) is None:
                    raise SchemeParserError("missing 'base_path'")
                scheme.base_path = "{base_path}/{run_path}/{test_type}".format(base_path = self.config.base_path, run_path = self.config.run_path, test_type = scheme.test_type)

            scheme.run_path = "{base_path}/{run_path}/{test_type}".format(base_path = self.config.base_path, run_path = self.config.run_path, test_type = scheme.test_type)
            scheme.ret_path = "{base_path}/{ret_path}/{test_type}".format(base_path = self.config.base_path, ret_path = self.config.ret_path, test_type = scheme.test_type)
            scheme.ret_raw_path = "{ret_path}/raw_result".format(ret_path = scheme.ret_path)
            scheme.src_path = "{base_path}/{ret_path}".format(base_path = self.config.base_path, ret_path = self.config.src_path)

            value = data.get('tool_tgz')
            if value is None:
                raise SchemeParserError("missing 'tool_tgz'")
            scheme.tool_tgz = value.format(base_path=self.config.base_path)

            value = data.get('tool_dir')
            if value is None:
                raise SchemeParserError("missing 'tool_dir'")
            scheme.tool_dir = value.format(base_path=scheme.base_path)

            value = data.get('tool_decompression')
            if value is None:
                raise SchemeParserError("missing 'tool_decompression'")

            scheme.tool_decompression = TestCmd(value, {"tool_tgz": scheme.tool_tgz, "tool_dir": scheme.tool_dir,
                        "base_path": scheme.base_path, "src_path": scheme.src_path}).cmd

            value = data.get('log_level')
            if value: 
                scheme.log_level = value

            value = data.get('log_file')
            if value:
                scheme.log_file = value.format(base_path=scheme.base_path)

            scheme.maxiterations = data.get('maxiterations', 1)

            scheme.rpm_list = data.get('rpm_list', [])

            value = data.get('configs')
            if value:
                self.parse_global_config(scheme, value)

            value = data.get('testcase')
            if value:
                self.parse_testcases(scheme, value if type(value) == list else [ value ])

            return scheme 
        except yaml.MarkedYAMLError as e: 
            logging.error(e)
            raise SchemeParserError(str(e))
        except yaml.YAMLError as e:
            logging.error(e)
            raise SchemeParserError(str(e))

    def parse_global_config(self, scheme, data):
        for item in data:
            name = item.get('name')
            if name is None:
                continue
            desc = item.get('desc', '')
            get_cmd = item.get('get')
            if get_cmd is None: 
                continue
            set_cmd = item.get('set')
            if set_cmd is None:
                continue
            value = item.get('value')
            if value is None:
                continue
            scheme.configs.append(TestConfig(name, desc, get_cmd, set_cmd, value))


    def parse_testcases(self, scheme, datas):
        if datas is None or len(datas) == 0:
            return

        for data in datas:
            clean = data.get('clean')
            if clean is None:
                logging.error('missing \'clean\' in testcase: {data}'.format(data=data))
                raise SchemeParserError("missing 'clean' in testcase")

            build = data.get('build')
            if build is None:
                logging.error('missing \'clean\' in testcase: {data}'.format(data=data))
                raise SchemeParserError("missing 'build' in testcase")

            testcmd = data.get('run')
            if testcmd is None:
                logging.error('missing \'run\' in testcase: {data}'.format(data=data))
                raise SchemeParserError("missing 'run' in testcase")

            tname = data.get('name')

            value = data.get('configs')
            if value is None or len(value) == 0:
                scheme.testcases.append(TestCase("{project}-{tstname}-0".format(project=scheme.project, tstname='null' if tname is None else tname), clean, build, testcmd))
            else:
                configs = self.parse_testcase_config(value)
                flag = data.get('schemeflag') 
                if flag:
                    self.parse_testcase_asm(scheme, tname, clean, build, testcmd, configs)
                else:
                    self.parse_testcase_sum(scheme, tname, clean, build, testcmd, configs)
        pass

    def parse_testcase_config(self, confs):
        data = {}
        for conf in confs:
            test_config = []
            name = conf.get('name')
            if name is None:
                continue

            get_cmd = conf.get('get') 
            if get_cmd is None:
                continue
            set_cmd = conf.get('set')
            if set_cmd is None: 
                continue
            desc = conf.get('desc', '')

            typ  = conf.get('type')
            if typ is None:
                continue
            elif typ == 'discrete':
                values = conf.get('values')
                if values is None:
                    continue
                for value in values:
                    test_config.append(TestConfig(name, desc, get_cmd, set_cmd, value))
            elif typ == 'continuous':
                values = conf.get('values') 
                if values and (len(values) == 2 or len(values) == 3):
                    for value in range(*values):
                        test_config.append(TestConfig(name, desc, get_cmd, set_cmd, value))
                items = conf.get('items')
                if items:
                    for value in items:
                        test_config.append(TestConfig(name, desc, get_cmd, set_cmd, value))
            else:
                continue

            if len(test_config) > 0:
                data[name] = test_config

        return data

    def parse_testcase_sum(self, scheme, tname, clean, build, testcmd, data):
        for key in data.keys():
            configs = data[key]
            for idx in range(len(configs)):
                name = "{project}-{config}-{index}".format(
                        project=(scheme.project if tname is None else "{}-{}".format(scheme.project, tname)), config=key, index=idx)
                testcase = TestCase(name, clean, build, testcmd)
                testcase.add_config(configs[idx])
                scheme.testcases.append(testcase)

    def parse_testcase_asm(self, scheme, tname, clean, build, testcmd, data):
        result = [] 
        for item in data.values(): 
            if len(result) == 0: 
                result = item
                continue
            it = itertools.product(item, result)
            result.clear()
            for m, n in it:
                if isinstance(n, tuple):
                    result.append((m, *n))
                else:
                    result.append((m, n))

        for idx in range(len(result)):
            name = "{project}-assemble-{index}".format(project=(scheme.project if tname is None else "{project}-{tname}".format(scheme.project, tname)), index=idx)
            testcase = TestCase(name, clean, build, testcmd)
            for tc in result[idx]:
                testcase.add_config(tc)
            scheme.testcases.append(testcase)
