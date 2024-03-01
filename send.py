import json
import requests
import platform

json_file="/root/kytuning/all_json_file.json"


# 读取 JSON 文件
with open(json_file, 'r') as f:
        json_data = f.read()
        # 将 JSON 字符串解析为 Python 对象
        data = json.loads(json_data)
        # 向 Python 对象中添加新的键值对
        data['user_name'] = "test"
        data['project_name'] = "test"
        data['arm'] = arm
        data['os_version'] = os_version
        # 将 Python 对象编码为新的 JSON 字符串
        new_json_data = json.dumps(data)
        # 发送 curl 请求
        url = 'http://192.168.22.20/kytuning/env/'
        headers = {
                    'User-Agent': 'curl/7.58.0',
                    'Accept': '*/*',
                    'Content-Type': 'application/json'
                    }

        response = requests.post(url, headers=headers, data=new_json_data)
        #print(new_json_data)
        # 输出服务器响应
        print(response.text)
