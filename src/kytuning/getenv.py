#!/usr/bin/env python3

import os
import json
import subprocess
import base64
import logging
from .exec_cmd import ExecCmd


_mode = None
_curenv = dict(os.environ, LC_ALL="C")


def exec_shell_cmd(command):
    """ 
    Launch shell subprocess to execute given command and return a 
    json-compatible str.

    On success, return the stdout msg with '\\n' and space striped.
    On fails, return null.
    """
    ret = subprocess.run(command, 
                         shell = True,
                         stdout = subprocess.PIPE, 
                         stderr = subprocess.PIPE, 
                         env = _curenv)
    if not ret.returncode:
        return ret.stdout.decode().strip("\n").strip()
    else:
        # commit: 18460c76776d23f5415ef5a98b3838ec15e21914
        if ret.returncode == 1 :
            return None 

        logging.error("cmd: [{0}]  msg: {1}".format(
            ret.args, ret.stderr))
        return None 


def base64_encode(s: str) -> str:
    """ 
    Encode the input str with base64.
    """
    if _mode == "debug":
        return "-----"

    encoded = base64.b64encode(s.encode('utf-8'))
    return str(encoded, 'utf-8')


class HardwareInfo:
    def __init__(self) -> None:
        try:
            self.lshw = json.loads(exec_shell_cmd("lshw -json -quiet"))
        # -J: export json
        # -o List: specify custom column
            self.lsblk = json.loads(exec_shell_cmd(
            "lsblk -d -J -o NAME,TYPE,VENDOR,MODEL,SIZE,ROTA,SCHED,RQ-SIZE,TRAN"))
        except:
            self.lshw = ''
            self.lsblk = ''
    def _dfs(self, root, hwclass, ret):
        if "class" not in root:
            return

        if hwclass == root["class"]:
            ret.append(root)
        else:
            if "children" in root:
                for child in root["children"]:
                    self._dfs(child, hwclass, ret)

    def get_hardwarelist_by_class(self, hwclass):
        ret = []

        self._dfs(self.lshw, hwclass, ret)

        return ret


    def get_manufacturer(self) -> str:
        res = exec_shell_cmd("dmidecode -t system | grep 'Manufacturer'")
        return res.split(':')[1].strip()

    def get_product(self) -> str:
        res = exec_shell_cmd("dmidecode -t system | grep 'Product Name'")
        return res.split(':')[1].strip()

    def get_serialnum(self) -> str:
        res = exec_shell_cmd("dmidecode -t system | grep 'Serial Number'")
        return res.split(':')[1].strip()

    # 整机信息
    def get_machineinfo(self) -> dict:
        result = {
            "manufacturer":  self.get_manufacturer(),
            "product":       self.get_product(),
            "serialnumber":  self.get_serialnum()
        }
        return result


    def get_bios(self) -> str:
        val = {
            "vendor":  exec_shell_cmd("dmidecode -s bios-vendor"),
            "version": exec_shell_cmd("dmidecode -s bios-version")
        }
        return val


    def get_memory(self) -> str:
        result = {
            'vendor':     self._get_mem_manufacture(),
            'mem_type':   self._get_mem_type(),
            'total_size': self._get_mem_total(),
            'mem_used':   self._get_mem_used(),
            'mem_count':  self._get_mem_count(),
            'mem_free':   self._get_mem_free(),
            'mem_freq':   self._get_mem_freq(),
            'swap':       self._get_mem_swap()
        }
        return result


    #获取内存品牌
    def _get_mem_manufacture(self) -> str:
        return exec_shell_cmd("dmidecode -t memory | grep 'Manufacturer:'|grep -v 'Not'|awk -F: '{print $2}'")

    #获取内存类型
    def _get_mem_type(self) -> str:
        return exec_shell_cmd("dmidecode -t memory | grep -v 'Unknown' | grep 'Type:' | sed 's/^[\t]*//' | grep -e '^Type:*' | awk -F: '{print $2}' | uniq")

    #获取内存总容量
    def _get_mem_total(self) -> str:
        return exec_shell_cmd("free -m | grep 'Mem:' | awk '{print $2}'") + " mebibytes"

    # 获取已使用的内存
    def _get_mem_used(self) ->str:
        return exec_shell_cmd("free -m | grep Mem: | awk '{print $3}'") + " mebibytes"
        

    # 获取空闲的内存
    def _get_mem_free(self) ->str:
        return exec_shell_cmd("free -m | grep Mem: | awk '{print $4}'") + " mebibytes"

    #获取内存数量
    def _get_mem_count(self) -> str:
        return exec_shell_cmd('dmidecode -t memory | grep Size: |grep MB | awk -F: "{print $2}" | wc -l')

    #获取内存频率
    def _get_mem_freq(self) -> str:
        return exec_shell_cmd("dmidecode -t memory |grep 'Configured .* Speed:'|awk -F: '{print $2}' | uniq")

    #获取swap分区大小信息
    def _get_mem_swap(self) -> str:
        return exec_shell_cmd("free -m | grep 'Swap:' | awk '{print $2}'") + " mebibytes"


    def get_numa_info(self) -> str:
        return exec_shell_cmd(
            "lscpu | grep NUMA | grep -v - | awk -F: '{print $2}'")

    # centos8 上的lsblk版本较低不支持获取分区表类型
    def get_parttable_type(self, dev) -> str:
        res = exec_shell_cmd(('fdisk -l %s | grep "Disklabel type"') % dev)
        if res == None:
            return None
        res = res.split(":")
        return res[1].strip()

    def get_fs_type(self, dev) -> str:
        res = exec_shell_cmd("df -Th | grep -E '%s$'" % dev)
        if res == None:
            return None

        res = res.split()
        result = ("%-6s %-6s %-6s %-6s %-6s") % (res[6], res[1], res[2], res[5], res[0])
        return result
        

    def get_disk(self) -> dict:
        result = []

        for blk in self.lsblk["blockdevices"]:
            if blk["type"] != "disk":
                continue
            val = {
                # 磁盘名
                "name": blk["name"],
                # 分区类型
                "part_type": self.get_parttable_type('/dev/' + blk['name']),
                # 获取厂商
                "vendor": blk["vendor"].strip() if blk["vendor"] else "Null",
                # 磁盘模式
                "model": blk["model"],
                # 空间大小
                "size": blk["size"],
                # 旋转性
                "rota": str(blk["rota"]),
                # IO调度器名称
                "sched": blk["sched"],
                # 请求队列大小
                "rq_size": blk["rq-size"],
                # 设备传输类型
                "tran": str(blk["tran"]),
                # 获取分区挂载点
                "mntpoint=/": self.get_fs_type('/'),
                "mntpoint=/home": str(self.get_fs_type('/home')),
            }
            result.append(val)
        return result


    def is_valid_nic(self, network) -> bool:
        return "logicalname" in network and \
            "product" in network and \
            "configuration" in network and \
            "speed" in network["configuration"] and \
            "ip" in network["configuration"]


    def get_nic_info(self):

        ret = []
        networklist = self.get_hardwarelist_by_class("network")

        for network in networklist:
            if self.is_valid_nic(network):
                val = {
                    "logicalname": network["logicalname"],
                    "product": network["product"],
                    "speed": network["configuration"]["speed"]
                }
                ret.append(val)

        return ret if ret else  []


    def get_cpu(self) -> str:
        cpu = {
               'Vendor ID':     self._get_cpu_vendor(),
               'CPU family':    self._get_cpu_family(),
               'model_name':    self._get_cpu_type(),
               'CPU MHz':       self._get_cpu_freq(),
               'CPU(s)':        self._get_cpu_phycount(),
               'Thread(s) per core':  self._get_cpu_cores_per(),
               'CPU Arch':      exec_shell_cmd('uname -p'),
               'CPU op-mode':   self._get_cpu_op_mode(),
               'Byte Order':    self._get_cpu_byte_order(),
               'On-line CPU(s) list': self._get_cpu_online_cpulist(),
               'Virtualization':self._get_cpu_virtual(),
               'Virtualization type':self._get_cpu_virtual_type(),
               'L1d cache:':    self._get_cpu_l1dcache(),
               'L1i cache':     self._get_cpu_l1icache(),
               'L2 cache':      self._get_cpu_l2cache(),
               'L3 cache':      self._get_cpu_l3cache(),
               'Flags':         self._get_cpu_flags()
        }
        return cpu


    def _get_cpu_vendor(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^Vendor ID" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_family(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^CPU family" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    #获取cpu型号
    def _get_cpu_type(self) -> str:
        return exec_shell_cmd("dmidecode -s processor-version | head -n 1")


    #获取cpu主频
    def _get_cpu_freq(self) -> str:
        return  exec_shell_cmd("cat /proc/cpuinfo |grep MHz|uniq | cut -d : -f 2");

    #获取物理cpu个数
    def _get_cpu_phycount(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^CPU(s)" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    #获取逻辑cpu个数
    def _get_cpu_cores_per(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "Thread(s) per core" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_op_mode(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "CPU op-mode" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_byte_order(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "Byte Order" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_online_cpulist(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "On-line CPU(s) list" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_virtual(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^Virtualization:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_virtual_type(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^Virtualization type:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_l1dcache(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^L1d cache:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_l1icache(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^L1i cache:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"
        
    def _get_cpu_l2cache(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^L2 cache:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_l3cache(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^L3 cache:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def _get_cpu_flags(self) -> str:
        result = ExecCmd(command = 'lscpu  | grep "^Flags:" | awk -F: \'{print $2}\'', env = _curenv).run()
        return result.stdout.lstrip() if result.exit_status == 0 else "nil"

    def get_hardware_info(self) -> dict:
        val = {
            "machineinfo":   self.get_machineinfo(),
            "bios":          self.get_bios(),
            "cpu":           self.get_cpu(),
            "memory":        self.get_memory(),
            #"numainfo":      self.get_numa_info(),
            "disk":          self.get_disk(),
            "nicinfo":       self.get_nic_info(),
        }

        return val


class SoftwareInfo:

    def _get_curr_utctime(self) -> str:
        result = ExecCmd(command = "date --utc", env = _curenv).run()
        return result.stdout if result.exit_status == 0 else result.stderr

    def _get_os_id(self) -> str:
        res = exec_shell_cmd('sed -n -e "/^ID=/p" /etc/os-release')
        result = res.replace('=', ' ').split()
        return result[1][1:-1]

    def _get_os_version(self) -> str:
        if self._get_os_id() == "kylin":
            release_file = '/etc/.productinfo'
            cmd = "sed -n -e '2p' %s" % release_file
            result = exec_shell_cmd(cmd)
        else:
            release_file = '/etc/os-release'
            cmd = "sed -n -e '/^VERSION=/p' %s" % release_file
            res = exec_shell_cmd(cmd)
            result = res.replace('=', ' ').split()[1]
        return result

    def _get_os_info(self) -> dict:
        val = {
            'curr UTC time':   self._get_curr_utctime(),
            "os_id":       self._get_os_id(),
            "os_arch":     exec_shell_cmd('uname -i'),
            "osversion":   self._get_os_version(),
            "kernel":      exec_shell_cmd('cat /proc/version'),
            "grub":        exec_shell_cmd('cat /proc/cmdline'),
        }
        return val

    def _get_sw_list(self) -> str:
        res = exec_shell_cmd('rpm -qa')
        return base64_encode(res)

    def _get_ipc_list(self) -> str:
        result = ExecCmd(command = "lsipc", env = _curenv).run()
        output = result.stdout if result.exit_status == 0 else result.stderr
        return base64_encode(output)

    def _get_conf_all(self) -> str:
        res = exec_shell_cmd('getconf -a')
        return base64_encode(res)

    def _get_sysctl_all(self) -> str:
        res = exec_shell_cmd("sysctl -a")
        return base64_encode(res)

    def _get_systemctl_info(self) -> str:
        res = exec_shell_cmd("systemctl list-unit-files  | tail -n +2")
        return base64_encode(res)

    def _get_driverinfo(self) -> str:
        res = exec_shell_cmd("cat /proc/modules | awk '{print $1}'")
        return base64_encode(res)

    def _get_gcc_ver(self) -> str:
        result = ExecCmd(command = "gcc --version | sed -n '1p' ", env = _curenv).run()
        return result.stdout if result.exit_status == 0 else result.stderr

    def _get_glibc_ver(self) -> str:
        flag = exec_shell_cmd("rpm -qa | grep glibc")
        if flag == "":
            return flag
        else:
            str = exec_shell_cmd('rpm -qi glibc')
            glibc_version = str.split()
            return glibc_version[5]

    def _get_java_ver(self) -> str:
        result = ExecCmd(command = 'java -version', env = _curenv).run()
        return result.stdout if result.exit_status == 0 else "nil"


    def _get_goo_ver(self) -> str:
        result = ExecCmd(command = 'g++ --version | sed -n "1p" ', env = _curenv).run()
        return result.stdout if result.exit_status == 0 else result.stderr

    def _get_gfortran_ver(self) -> str:
        result = ExecCmd(command = 'gfortran --version | sed -n "1p"', env = _curenv).run()
        return result.stdout if result.exit_status == 0 else "nil"


    def _get_python_ver(self) -> str:
        flag = exec_shell_cmd("rpm -qa | grep python")
        if flag == "":
            return flag
        else:
            return exec_shell_cmd('python3 --version')

    #获取selinux状态
    def _get_selinux_status(self) -> str:
        return exec_shell_cmd('getenforce')

    #获取电源管理状态
    def _get_power_status(self) -> str:
        return exec_shell_cmd('cat /sys/power/state')

    #获取cpu调度策略
    def _get_cpu_sched(self) -> str:
        str = exec_shell_cmd('chrt -p 1|grep -i sched')
        cpu_sched = str.split()
        return cpu_sched[5]

    
    # 重要软件版本信息
    def _get_sw_ver_info(self) -> dict:
        result = {
            "gccversion":       self._get_gcc_ver(),
            "glibcversion":     self._get_glibc_ver(),
            "javaversion":      self._get_java_ver(),
            "g++version":       self._get_goo_ver(),
            "gfortranversion":  self._get_gfortran_ver(),
            "pythonversion":    self._get_python_ver(),
        }
        return result
    def _get_loadavg(self) -> str:
        result = ExecCmd(command = 'cat /proc/loadavg', env = _curenv).run()
        return result.stdout if result.exit_status == 0 else result.stderr

    def _get_uptime(self) -> str:
        result = ExecCmd(command = "uptime  | awk  '{print $3 $4 $5}'", env = _curenv).run()
        return result.stdout if result.exit_status == 0 else result.stderr
        
        
    def _get_runtime_env(self) -> dict:
        val = {
            "sysconf":         self._get_conf_all(),
            "sysctl":          self._get_sysctl_all(),
            "systemctlinfo":   self._get_systemctl_info(),
            "driverinfo":      self._get_driverinfo(),
            "rpmlist":         self._get_sw_list(),
            "ipclist":         self._get_ipc_list(),
            "selinux_status":  self._get_selinux_status(),
            "power_status":    self._get_power_status(),
            "cpu_sched":       self._get_cpu_sched(),
            'loadavg':         self._get_loadavg(),
            'uptime':          self._get_uptime()
        }
        return val
    
    def get_software_info(self) -> dict:
        val = {
            'os':              self._get_os_info(),
            'runtime':         self._get_runtime_env(),
            'software_ver':    self._get_sw_ver_info(),
        }
        return val


class NetworkInfo:
    def __init__(self, hw: HardwareInfo) -> None:
        self.hw = hw

    def get_network_info(self) -> dict:
        ret = []
        networklist = self.hw.get_hardwarelist_by_class("network")

        for network in networklist:
            if self.hw.is_valid_nic(network):
                nicname = network["logicalname"]
                fields = {
                    "IP4.GATEWAY": "gateway",
                    "GENERAL.MTU": "mtu",
                }
                nmcli_info = {}
                for key in fields.keys():
                    nmcli_info[fields[key]] = exec_shell_cmd(
                        "nmcli -g {0} device show {1}".format(key, nicname))

                val = {
                    "nicname": network["logicalname"],
                    "ip":      network["configuration"]["ip"],
                    "hwaddr":  network["serial"],
                    "gateway": nmcli_info["gateway"],
                    "mtu":     nmcli_info["mtu"],
                }
                ret.append(val)

        return ret if ret else  {"nic":[]}

    def get_network(self) ->dict:
        val = {
            'nic': self.get_network_info()
        }
        return val


class EnvManager(object):
    def __init__(self, ctrl = None):
        self.ctrl = None
        self.hwinfo = HardwareInfo()
        self.swinfo = SoftwareInfo()
        self.nwinfo = NetworkInfo(self.hwinfo)

    def get_env_info(self):
        env_info = {
            'hwinfo': self.hwinfo.get_hardware_info(),
            'swinfo': self.swinfo.get_software_info(),
            'nwinfo': self.nwinfo.get_network(),
        }
        return env_info

    # 将环境信息导出为字典
    def export_env_dict(self) -> dict:
        return {"envinfo": self.get_env_info()}
    
    # 导出环境信息到Json
    def collect(self):
        try:
            info_json = json.dumps(self.export_env_dict(), indent = 2)
        except:
            logging.error("export env info to json failed!")
        return info_json


if __name__ == '__main__':
    _mode = "debug"
    data = EnvManager().collect()
    print(data)

