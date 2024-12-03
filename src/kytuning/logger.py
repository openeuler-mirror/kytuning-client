"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: wangqingzheng <wangqingzheng@kylinos.cn>
 * Date: Thu Dec 14 11:15:54 2023 +0800
"""
import logging



def log_init(path='kytuning.log', levelname='info'):
    if path is None or len(path) == 0:
        path = 'kytuning.log'
    level = logging.INFO
    if levelname == 'error':
        level = logging.ERROR
    elif levelname == 'warning':
        level = logging.WARN
    elif levelname == 'debug':
        level = logging.DEBUG
    Format = '[%(levelname)s][%(asctime)s,%(module)s,%(lineno)d,%(funcName)s] %(message)s'
    logging.addLevelName(logging.DEBUG, 'D')
    logging.addLevelName(logging.INFO, 'I')
    logging.addLevelName(logging.WARNING, 'W')
    logging.addLevelName(logging.ERROR, 'E')
    logging.basicConfig(filename=path, level=level , format=Format, filemode='w')

if __name__ == '__main__':

    log_init()

    logging.error('Hello')
