import subprocess


def update_project_message(service):
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


def iterative_test(service_lsit):
    for service in service_lsit:
        systemctl_command = "systemctl start {}".format(service)
        systemctl_result = subprocess.run(systemctl_command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          text=True)
        print(systemctl_result.stdout)
        if systemctl_result.returncode:
            return "systemctl start {} 命令执行失败".format(service)
        update_project_message(service)
        run_command = "cd /root/run_kytuning-ffdev/;bash run.sh"
        subprocess.run(run_command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


# egg:service_lsit = ['sshd.service', 'NetworkManager.service']
service_lsit = []
iterative_test(service_lsit)