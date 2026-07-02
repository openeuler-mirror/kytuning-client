#!/bin/bash
# 声明安装包的关联数组
declare -A pip_dict
# 增加所需要下载的pip名称和对应包名称
pip_dict["yaml"]="PyYAML-6.0.tar.gz"
pip_dict["openpyxl"]="openpyxl-3.0.9.tar.gz"
pip_dict["et_xmlfile"]="et_xmlfile-1.1.0.tar.gz"
# requests 依赖 certifi
pip_dict["certifi"]="certifi-2024.2.2.tar.gz"
pip_dict["requests"]="requests-2.31.0.tar.gz"


python3 create-site-packages.py

for key in "${!pip_dict[@]}"; do
  echo "Key: $key, Value: ${pip_dict[$key]}"
  python3 -c "import $key" 2>/dev/null
  result=$?
  if [[ $result -ne 0 ]]; then
    echo "$key is not installed"
    tar -xvf ${pip_dict[$key]} > /dev/null
    dname=`echo ${pip_dict[$key]} |sed s/\.tar\.gz//g`
    pushd $dname
    python3 setup.py install
    popd
    rm -rf $dname
  fi
done
