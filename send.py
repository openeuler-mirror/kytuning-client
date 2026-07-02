"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: liyl_kl <liyulong@kylinos.cn>
 * Date: Fri Mar 1 15:05:49 2024 +0800
"""
# -*- coding: utf-8 -*-
import re
import sys
import json
import requests

if len(sys.argv) < 2:
    print("上传数据错误")
    print("方法:")
    print("python3 send.py {配置文件路径} {json文件的绝对路径}")
    print("请检查配置文件路径、和json文件路径是否正确")
    sys.exit(1)

CONFIF_FILE = sys.argv[1]
json_file = sys.argv[2]

# 读取文件内容
with open(CONFIF_FILE, encoding='utf-8') as f:
    file_content = f.read()

# 去除以#开头的注释行
lines = file_content.split('\n')
filtered_lines = [line for line in lines if not line.strip().startswith('#')]
filtered_content = '\n'.join(filtered_lines)

# 使用正则表达式匹配键值对
pattern = re.compile(r'^(.*?)=(.*?)$', re.MULTILINE)
matches = pattern.findall(filtered_content)

config = dict(matches)

# 获取对应的键值
rk_benchmark = config.get('rk_benchmark')
project_name = config.get('project_name')
username = config.get('username')
password = config.get('password')
token = config.get('token')
kytuning_web_url = config.get('kytuning_web_url')
test_case_id = config.get('test_case_id')

if not token:
    login_url = kytuning_web_url + '/kytuning/api-token-auth/'
    response = requests.post(login_url,data={'username':username,'password':password}, verify=False)
    if response.status_code != 200:
        print("请确认账号密码正确！")
        exit(0)
    token = 'Bearer ' + response.json()['token']
# 读取 JSON 文件
with open(json_file, 'r') as f:
        json_data = f.read()
        # 将 JSON 字符串解析为 Python 对象
        data = json.loads(json_data)
        # 向 Python 对象中添加新的键值对
        data['user_name'] = username
        data['project_name'] = project_name
        data['test_case_id'] = test_case_id
        # 将 Python 对象编码为新的 JSON 字符串
        new_json_data = json.dumps(data)
        # 发送 curl 请求
        create_url = kytuning_web_url + '/kytuning/env/'
        headers = {
                    'User-Agent': 'curl/7.58.0',
                    'Accept': '*/*',
                    'Content-Type': 'application/json',
                    'Authorization': token
                    }

        response = requests.post(create_url, headers=headers, data=new_json_data, verify=False)
        # 输出服务器响应
        print(json.loads(response.content.decode('utf-8')))
