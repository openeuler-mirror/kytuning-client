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

