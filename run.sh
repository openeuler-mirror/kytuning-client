#!/bin/bash

source conf/user.cfg
ARCH=$(arch)
WGET_BIN="wget -c -P"
UPLOAD="True"

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
	base_dir=`grep base_path conf/kytuning.yaml |cut -d':' -f 2|sed 's/\"//g'`
	run_dir=$base_dir/run
	
	cur_path=$(cd $(dirname $0); pwd)
	tools_path=$cur_path/tools

	if [ ! -d ${tools_path} ]; then
		mkdir ${tools_path} 
	fi
	file1="$base_dir/all_json_file.json"
	if [  -f $file1 ];then
		file2="$base_dir/all_json_file-"`date +"%Y%m%d%H%M%S"`".json"
		mv $base_dir/all_json_file.json $file2
        fi
	
	opt_use_net=0
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
	while getopts "f:h" opt; do
	#echo $opt $OPTARG
		case $opt in
		f)
			run "$rk_benchmark" $OPTARG
			exit 0
			;;
		v)
			usage
			exit 0
			;;
		*)
			usage	
			exit 1
			;;
		esac
	done
	usage 
	exit 1	
}

# 下载lmbench.tar cpu2006.tar cpu2017.tar jvm2008.tar需要单独处理
# 接受3个参数, $1是tar文件所在目录，$2是tar文件, $3是文件服务器
function handle_single_benchmark() {
	local var_path=$1
	local var_file=$2
	local var_server=$3

	${WGET_BIN} ${var_path} ${var_server}${var_file}
	if [ $? -ne 0 ]; then
		echo "下载${var_file}失败"
		exit 1
	fi
	
	tar xvf ${var_path}/${var_file} -C ${var_path}
	if [ $? -eq 0 ]; then
		rm -f ${var_path}/${var_file}	
	else
		echo "解包文件失败：${var_path}/${var_file}"
		exit 1
	fi 
}

# 从网络下载benchmark工具，接受一个参数
function download() {
	local benchmark=$1
	local file_server="http://192.168.15.46/tools/"
	case ${benchmark} in
	unixbench)
		if [ ! -f ${tools_path}/UnixBench5.1.3-1.tar.gz ]; then
			${WGET_BIN} ${tools_path} ${file_server}UnixBench5.1.3-1.tar.gz
		fi
		;;
	lmbench)
		if [ ! -f ${tools_path}/lmbench-3.0-a9-2.tar.bz2 ]; then
			handle_single_benchmark ${tools_path} lmbench.tar "${file_server}"	
		fi
		;;
	stream)
		if [ ! -f ${tools_path}/stream-5.9-1.tar.bz2 ]; then
			${WGET_BIN} ${tools_path} ${file_server}stream-5.9-1.tar.bz2
		fi
		;;
	fio)
		if [ ! -f ${tools_path}/fio-3.20.tar.bz2 ]; then
			${WGET_BIN} ${tools_path} ${file_server}fio-3.20.tar.bz2
		fi
		;;
	iozone)
		if [ ! -f ${tools_path}/iozone3_430.tar ]; then
			${WGET_BIN} ${tools_path} ${file_server}iozone3_430.tar
		fi
		;;
	cpu2006)
		if [[ ! "${ARCH}" == "loongarch64" && ! -f ${tools_path}/cpu2006-1.2-pf01.iso ]]; then
			handle_single_benchmark ${tools_path} cpu2006.tar "${file_server}"
		elif [[ "${ARCH}" == "loongarch64" &&  ! -f ${tools_path}/cpu2006-1.2-lg64.tar.gz ]];then
			${WGET_BIN} ${tools_path} ${file_server}cpu2006-1.2-lg64.tar.gz
		fi
		;;
	cpu2017)
		if [ ! -f ${tools_path}/cpu2017-1_0_5.iso ]; then
			${WGET_BIN} ${tools_path} ${file_server}cpu2017.tar
			handle_single_benchmark ${tools_path} cpu2017.tar "${file_server}"	
		fi
		;;
	jvm2008)
		if [ ! -f ${tools_path}/SPECjvm2008_1_01_setup.jar ]; then
			handle_single_benchmark ${tools_path} jvm2008.tar "${file_server}"	
		fi
		;;
	*)
		echo "无法下载${benchmark}, 目前尚未支持该工具"
		exit 1
		;;
	esac
}

# 解压指定的本地benchmark工具包，
# 如果在命令行中使用-f制定了本地文件，或者在user.cfg配置了本地文件，调用该函数处理
function handle_tarfile() {
	tar xv --skip-old-files -f $1  
    tar -xvf ${tools_path}/lmbench.tar -C ${tools_path}
    tar -xvf ${tools_path}/cpu2006.tar -C ${tools_path}
    tar -xvf ${tools_path}/cpu2017.tar -C ${tools_path}
    tar -xvf ${tools_path}/jvm2008.tar -C ${tools_path}

}

install_dependencies() {
    # Install dependencies
    local packages=""
    local packages_manager=""
    local packages_manager_install=""
	local rk_benchmark=$1
	declare -A packages_dict ## keys:benchmark values:packages
	packages_dict[all_dep]="python3"

	if [[ ${rk_benchmark} == *unixbench* ]]; then
		packages_dict[unixbench]="perl-Time-HiRes"
	fi
	if [[ ${rk_benchmark} == *lmbench* ]]; then
		packages_dict[lmbench]="expect libtirpc-devel"
	fi
	if [[ ${rk_benchmark} == *jvm2008* ]]; then
		packages_dict[jvm2008]="java-1.8.0-openjdk-devel"
	fi
	if [[ ${rk_benchmark} == *cpu20* ]]; then
		packages_dict[cpu20xx]="gcc-c++ gcc-gfortran"
		test ! -e /lib64/libnsl.so.1 && test ${opt_use_net} -eq 0 && ln -sf /lib64/libnsl.so.2 /lib64/libnsl.so.1
	fi

    if [ `command -v yum` ];then
        packages_manager="rpm -q"
        packages_manager_install="yum"
		test ${opt_use_net} -eq 1 && packages_dict[all_dep]="python3-pip libnsl ${packages_dict[all_dep]}"	
    elif [ `command -v apt-get` ];then
        packages_manager="dpkg -s"
        packages_manager_install="sudo apt-get"
		if [[ "${packages_dict[cpu20xx]}x" != "x" ]]; then
			packages_dict[cpu20xx]="g++ gfortran"
		fi
		if [[ "${packages_dict[jvm2008]}x" != "x" ]]; then
			packages_dict[jvm2008]="openjdk-8-jre-headless"
		fi
		test ${opt_use_net} -eq 1 && packages_dict[all_dep]="python3-pip libnsl ${packages_dict[all_dep]}"	
    fi
	
    for package in ${packages_dict[@]}; do
        if ! $packages_manager $package > /dev/null; then
            $packages_manager_install install -y $package
        fi
        if [ $? -ne 0 ]; then
            echo "Failed to install $package"
            exit 1
        fi
    done

    # install python modules
}

# 运行业务, 接受1个参数或2个参数
# 参数1，必须，将要运行的benchmark列表
# 参数2，非必须，本地benchmark工具包文件
function run() {
	local testlist=$1
	local localfile=$2	

	# 下载benchmark工具或使用本地benchmark工具包文件
	if [ $localfile ]; then
		opt_use_net=0
		echo "指定了本地文件 ${localfile}"
		handle_tarfile ${localfile}
	elif [ $rk_toolspath ]; then
		opt_use_net=0
		echo "配置了本地文件 ${rk_toolspath}"
		handle_tarfile ${rk_toolspath}
	else
		for bc in ${testlist}; do
			echo 下载 ${bc}
			download ${bc}
		done	
	fi		
	
	# 安装benchmark工具到/root/kytuning目录，实际上只是建立一个链接 
    if [ ! -e $base_dir/tools ]; then
	    mkdir $base_dir
        ln -sf $tools_path $base_dir/tools
		echo "安装benchmark到${base_dir}/tools"
    fi
	#安装benchmark依赖
	install_dependencies ${rk_benchmark}
    # Run kytuning
    for bc in $rk_benchmark; do
        cd $cur_path
		if [[ ${bc} == "cpu2006" && ${ARCH} == "loongarch64" ]]; then
			  bc=${bc}-${ARCH}
		fi 
        if [ -f $cur_path/yaml-base/$bc-base.yaml ]; then
            python3 $cur_path/src/kytuning.py $cur_path/yaml-base/$bc-base.yaml
			sync
            echo 3 > /proc/sys/vm/drop_caches
            sleep 10
        fi
    done
}

	
# 程序入口
function main() {
	init

	if [ $# -eq 0 ]; then
		run "$rk_benchmark"
		if [ $? -eq 0 ] && [ $UPLOAD="true" ] ;then
		    sed -i 's/NR\/RE//g' $base_dir/all_json_file.json
		    python3 ./send.py $base_dir/all_json_file.json
		fi
	else
		parse_cmd $@
	fi
}

main $@

