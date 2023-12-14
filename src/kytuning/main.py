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
                scheme = SchemeParser().parse(f) 
                scheme.prepare()
            except SchemeError as e:
                print(e)
                sys.exit()
            except SchemeParserError as e:
                print(e)
                sys.exit() 
        try:
            self.test = TestFactory().get_test_object(scheme.get_test_type(), scheme)
            self.test.prepare() 
        except TestNotFound as e:
            logging.error(e)
            sys.exit()
        except SchemeError as e:
            logging.error(e)
            sys.exit()

        try:
            self.test.collect_env() 
            self.test.install_dependent_rpms() 
            self.test.setup_config(); 
            self.test.do_test() 
        except TestCaseError as e:
            logging.error(e)
        except Exception as e:
            logging.error(e)
        except BaseException as e:
            logging.error(e)
        finally: 
            self.test.reset_config(); 
            self.test.remove_dependent_rpms()
            self.test.export()
            logging.info('all tests are finshed.')

if __name__ == '__main__':
    Main().run()
