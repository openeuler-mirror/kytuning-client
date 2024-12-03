"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: wangqingzheng <wangqingzheng@kylinos.cn>
 * Date: Thu Dec 14 10:52:28 2023 +0800
"""


__all__ = ['KyTuningError', 'KyTuningNoSuchDir']


class KyTuningError(Exception):
    pass


class KyTuningNoSuchDir(Exception):
    pass


class SchemeParseError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(*args, **kwargs)
