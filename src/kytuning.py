"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl <liyulong@kylinos.cn>
 * Date: Thu Dec 7 16:05:49 2023 +0800
"""
#!/usr/bin/python3

import kytuning

if __name__ == '__main__':
    try:
        kytuning.Main().run()
    except Exception as e:
        print(e)
