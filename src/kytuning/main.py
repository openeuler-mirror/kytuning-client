__all__ = [ 'Main' ]

import sys

from .logger import *
from .scheme import *
from .test import *
from .error import *


class Main(object):
    def __init__(self):
        self.test= None

    def run(self): 
        if len(sys.argv) < 2: 
            print('input scheme path.') 
            sys.exit()

        path = sys.argv[1] 
        if path is None or len(path) == 0: 
            print('invalid scheme path : "%s"' % path) 
            sys.exit()

        with open(path, 'r') as f: 
            try:
            except SchemeError as e:
                sys.exit()
            except SchemeParserError as e:
                print(e)
                sys.exit() 

if __name__ == '__main__':
    Main().run()
