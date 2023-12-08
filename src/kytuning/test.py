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
