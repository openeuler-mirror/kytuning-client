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

