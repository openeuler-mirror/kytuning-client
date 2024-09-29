import re
import subprocess


def get_service_list(target):
    """
    获取target对应的服务
    """
    output = subprocess.check_output(['systemctl', 'list-dependencies', target]).decode().splitlines()
    service_list = []

    for line in output:
        cleaned_line = re.sub(r'^[● │ └─ ├─]*', '', line).strip()
        if cleaned_line.endswith(('target', 'service')):
            service_list.append(cleaned_line)
    return service_list


def update_project_message(service):
    """
    更新project信息
    """
    with open('./conf/kytuning.cfg', 'r') as file:
        lines = file.readlines()
    new_lines = []
    for line in lines:
        if line.startswith('project_message='):
            current_project_message = line.split('=')[1].strip().strip('"')  # 获取当前的 project_message
            new_project_message = f'{current_project_message}、{service}' if current_project_message else f'{service}'
            new_lines.append(f'project_message="{new_project_message}"\n')
        else:
            new_lines.append(line)
    with open('./conf/kytuning.cfg', 'w') as file:
        file.writelines(new_lines)
    print(f'更新project_message配置信息成功')


def iterative_test(service_list):
    """
    迭代测试
    """
    # 需要服务倒叙运行
    print(f'因为服务的树结构所以需要倒叙运行相关服务')
    for service in service_list[::-1]:
        systemctl_command = "systemctl start {}".format(service)
        systemctl_result = subprocess.run(systemctl_command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(systemctl_result.stdout)
        if systemctl_result.returncode:
            print(f'systemctl start {service} 命令执行失败，启动下一服务')
            continue
        print(f'systemctl start {service} 命令运行成功')
        update_project_message(service)
        run_command = "cd /root/run_kytuning-ffdev/;bash run.sh"
        subprocess.run(run_command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f'启动{service}后，性能测试运行成功')


# 获取服务列表
service_list = get_service_list('graphical.target')
print(f'graphical.target对应的targethe服务为：{service_list}')
# service_list = ['sshd.service', 'NetworkManager.service']
# 拉起各项服务后测试
iterative_test(service_list)
