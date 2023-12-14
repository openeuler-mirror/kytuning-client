import os
import time
import yaml
import json
import logging
import itertools
import subprocess
from subprocess import SubprocessError

from .logger import log_init

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

def subproc_call(command, timeout=None, check=False):
    return subprocess.run(command, shell=True, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8', timeout=timeout, check=check)

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
                r = subproc_call(self.get_cmd)
                if r.returncode:
                    raise TestConfigError(r.returncode)
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
        self.test_cmd = test_cmd 
        self.build_cmd = build_cmd
        self.clean_cmd = clean_cmd
        self.configs = []

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
        return data;

    def to_data(self):
        data = { 'name' : self.name, 'build' : self.build_cmd, 'clean' : self.clean_cmd, 'run' : self.test_cmd }
        configs = []
        for e in self.configs:
            configs.append(e.to_data())
        data['configs'] = configs
        return data


