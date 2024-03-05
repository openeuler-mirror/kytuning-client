import sys
import json
import requests

project_name="麒麟自测1"
user_name = "李四"

if len(sys.argv) < 2:
    print("请追加all_json_file文件路径")
    print("例如:")
    print("python3 send.py /root/kytuning/all_json_file.json")
    print("")
    sys.exit(1)
    
json_file=sys.argv[1]

# 读取 JSON 文件
with open(json_file, 'r') as f:
        json_data = f.read()
        # 将 JSON 字符串解析为 Python 对象
        data = json.loads(json_data)
        # 向 Python 对象中添加新的键值对
        data['user_name'] = user_name
        data['project_name'] = project_name
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
