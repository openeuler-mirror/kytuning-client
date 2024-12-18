"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl <liyulong@kylinos.cn>
 * Date: Fri Dec 8 17:18:33 2023 +0800
"""
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
            logging.error('input scheme path.') 
            sys.exit()

        opts, args = getopt.getopt(sys.argv[1:], "hf:", ["help", "report_path="])
        for o, a in opts:
            if o in ("-h", "--help"):
                sys.exit()
            elif o in ("-f", "--report_path"):
                self.config.add({'main':{'report_path': a}})
            pass

        if len(args) == 0:
            logging.error('input scheme path.')
            sys.exit()

        for file in args:
            if file is None or len(file) == 0:
                logging.error('invalid scheme path : "%s"' % file)
                sys.exit()
            if not os.path.exists(file):
                logging.error("scheme not found: \"%s\"" % file)
                sys.exit()

        return args

    def run(self): 
        # 解析参数
        paths = self.__parse_argv()
        # do test
        cpaths = len(paths)
        for idx in range(cpaths):
            try:
                test = TestFactory().get(paths[idx])  # 配置文件和文件夹的准备
                test.prepare()  # 软件环境验证、初始化保存文件的对象
                test.do_test()  # 环境、安装软件、设置配置文件、运行测试
                test.export(self.config.report_path)  # 测试结果保存接口
            except SchemeError as e:
                logging.error(e)
            except SchemeParserError as e:
                logging.error(e)
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


if __name__ == '__main__':
    Main().run()
