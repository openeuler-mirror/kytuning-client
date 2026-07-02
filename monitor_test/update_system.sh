#!/bin/bash

# 第一步需要手动配置对应的kojifiles源

# 需要配置否则定时任务是会导致获取环境信息失败
export PATH=/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin

# 使用yum获取更新列表，去除标题行，提取包名，然后去除最后一个点号及之后的内容
updates=$(yum list updates | grep -v "Available" | grep -v "Last" | awk '{print $1}' | sed 's/\.[^.]*$//')

rm -rf package_list.txt
update=false
echo 'rpm包更新开始时间----->'`date` >> package_list.txt
for package in $updates; do
    update=true
    echo "rpm包版本迭代记录-----" >> package_list.txt
    echo `rpm -qa | grep ^$package` >> package_list.txt
    yum install $package -y
    echo `rpm -qa | grep ^$package` >> package_list.txt
done
echo $update
if [ "$update" = true ];then
  cd /root/run_kytuning-ffdev/;bash ./run.sh
  # 获取配置文件中的项目名称信息
  python3 /root/run_kytuning-ffdev/monitor_test/send_url_message.py
fi
