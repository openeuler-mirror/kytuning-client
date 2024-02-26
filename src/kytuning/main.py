__all__ = [ 'Main' ]

import sys, getopt, os, time

from .logger import *
from .scheme import subproc_call, SchemeError, SchemeParserError, TestCaseError
from .test import *
from .error import *
from .config import *

class Main(object):
    def __init__(self):
        # 载入配置文件
        self.config = KYConfig().load()

    def __parse_argv(self):
        if len(sys.argv) < 2: 
            print('input scheme path.') 
            sys.exit()

        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "report_path="])
        for o, a in opts:
            if o in ("-h", "--help"):
                sys.exit()
            elif o in ("-f", "--report_path"):
                self.config.add({'main':{'report_path': a}})
            pass

        if len(args) == 0:
            print('input scheme path.')
            sys.exit()

        for file in args:
            if file is None or len(file) == 0:
                print('invalid scheme path : "%s"' % file)
                sys.exit()
            if not os.path.exists(file):
                print("scheme not found: \"%s\"" % file)
                sys.exit()

        return args

    def run(self): 
        # 解析参数
        paths = self.__parse_argv()
        # do test
        cpaths = len(paths)
        for idx in range(cpaths):
            try:
                test = TestFactory().get(paths[idx])
                test.prepare()
                test.do_test()
                test.export(self.config.report_path)
            except SchemeError as e:
                print(e)
                sys.exit()
            except SchemeParserError as e:
                print(e)
            except TestNotFound as e:
                logging.error(e)
            except TestCaseError as e:
                logging.error(e)
            except Exception as e:
                logging.error(e)
            except BaseException as e:
                logging.error(e)
            finally:
                if (cpaths > 1) and ((idx + 1) < cpaths):
                    subproc_call("echo 3 > /proc/sys/vm/drop_caches")
                    time.sleep(10)
        pass

        logging.info('all tests are finshed.')

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
