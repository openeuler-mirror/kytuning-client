#!/bin/bash

source conf/user.cfg

# 本文件使用的变量
base_dir=
run_dir=
cur_path=
tools_path=

# 命令行选项开关
# 使用网络开关，1表示使用网络，0表示不使用网络，默认使用网络
opt_use_net=

# 初始本文件头部定义的变量
function init() {
}

# 显示使用帮助
function usage() {
	echo "usage:
    $0
	不带参数运行，默认从网络上下载benchmark工具包

    $0 -f filename 
        指定benchmark工具包文件，指定后将不会从网络下载benchmark工具

    $0 -h
        显示本帮助" 
}

# 解析命令行参数
function parse_cmd() {
	exit 1	
}

# 程序入口
function main() {
	init

	if [ $# -eq 0 ]; then
		run "$rk_benchmark"
	else
		parse_cmd $@
	fi
}

main $@

