"""
 * Copyright (c) KylinSoft  Co., Ltd. 2024.All rights reserved.
 * PilotGo-plugin licensed under the Mulan Permissive Software License, Version 2. 
 * See LICENSE file for more details.
 * Author: wangqingzheng <wangqingzheng@kylinos.cn>
 * Date: Thu Dec 14 10:56:24 2023 +0800
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 功能：从环境/测试结果json文件导出到excel
# 依赖库：openpyxl

__all__ = ['Export']

import os
import re
import json
import difflib
import argparse

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
TOOL_NAME_UB = "Unixbench"
TOOL_NAME_CPU06 = "Speccpu2006"
TOOL_NAME_CPU17 = "Speccpu2017"
TOOL_NAME_IOZONE = "Iozone"
TOOL_NAME_JVM08 = "Specjvm2008"
TOOL_NAME_LMB = "Lmbench"
TOOL_NAME_STREAM = "Stream"
TOOL_NAME_NETPERF = "Netperf"
TOOL_NAME_FIO = "Fio"


class BenchMark(object):
    def __init__(self):
        super().__init__()
        self.items = None
        self.tool_name = None
        self.tool_version = None  # 暂时未使用
        self.sheet_env_title = "性能测试环境"
        self.index_start = 1
        self.text_cmd = "执行命令:"
        self.text_modify_args = "修改参数:"
        self.value_cmd = "测试None"
        self.value_modify_args = "测试None"


class Unixbench(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_UB
        self.items = ["Dhrystone 2 using register variables(lps)",
                      "Double-Precision Whetstone(MWIPS)",
                      "Execl Throughput(lps)",
                      "File Copy 1024 bufsize 2000 maxblocks(KBps)",
                      "File Copy 256 bufsize 500 maxblocks(KBps)",
                      "File Copy 4096 bufsize 8000 maxblocks(KBps)",
                      "Pipe Throughput(lps)",
                      "Pipe-based Context Switching(lps)",
                      "Process Creation(lps)",
                      "Shell Scripts (1 concurrent)(lpm)",
                      "Shell Scripts (8 concurrent)(lpm)",
                      "System Call Overhead(lps)",
                      "Index Score(sum)"]
        self.thread = ["单线程", "多线程"]
        self.cmd = "执行命令："
        self.modify_argv = "修改参数："
        self.cpu_num_flag = "in system; run"
        self.thread_flag = "1 parallel"
        self.read_items_flag = "BASELINE"

    def ret_to_dict(self, file: str):
        """测试结果解析"""
        ret_dict = {"tool_name": self.tool_name}
        _thread = ''
        _max_thread = ''
        _read_flag = False
        score_list = ['' for i in self.items]
        with open(file, 'r') as f:
            file_lines = f.readlines()
        for line in file_lines:
            if self.cpu_num_flag in line:
                maxcpu = re.findall(
                    r"-?\d+\.?\d*e?-?\d*?", line)[0]
                _max_thread = maxcpu + " parallel"
            if self.thread_flag in line:
                _thread = self.thread[0]
                continue
            elif _max_thread in line:
                _thread = self.thread[1]
                continue
            if self.read_items_flag in line:
                _read_flag = True
                continue
            if _read_flag:
                _score_list = score_list
                for i, key in enumerate(self.items):
                    if key[:-7] in line:
                        temp = re.findall(r"-?\d+\.?\d*e?-?\d*?", line)
                        if temp:
                            _score_list[i] = temp[-1]
                        elif "==" not in line:
                            _score_list[i] = ''
                        if key == self.items[-1]:
                            ret_dict[_thread] = dict(
                                zip(self.items, _score_list))
                            _read_flag = False
                            break
        if len(ret_dict.keys()) > 1:
            return ret_dict
        else:
            return None


class Speccpu2006(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_CPU06
        self.dtype = ["fp", "int"]
        self.tune = ["base", "peak"]
        self.items = {
            self.dtype[0]: ["410.bwaves", "416.gamess",
                            "433.milc", "434.zeusmp",
                            "435.gromacs", "436.cactusADM",
                            "437.leslie3d", "444.namd",
                            "447.dealII", "450.soplex",
                            "453.povray", "454.calculix",
                            "459.GemsFDTD", "465.tonto",
                            "470.lbm", "481.wrf",
                            "482.sphinx3", "SPECfp_2006"],
            self.dtype[1]: ["400.perlbench", "401.bzip2",
                            "403.gcc", "429.mcf", "445.gobmk",
                            "456.hmmer", "458.sjeng",
                            "462.libquantum", "464.h264ref",
                            "471.omnetpp", "473.astar",
                            "483.xalancbmk", "SPECint_2006"]}
        self.thread = ["单线程", "多线程"]

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name, "items": {}}
        ret_names_json = None
        with open(file, 'r') as f:
            try:
                ret_names_json = json.loads(f.read())
            except Exception as e:
                print("json 文件打开失败!", e)
                return None
        for _file in list(ret_names_json.values()):
            if len(_file) == 0:
                continue
            _file_lines = _file.split("\n")
            _thread = None
            _read_flag = False
            _type = None
            _items_list = []
            _scores_tune = {self.tune[0]: [], self.tune[1]: []}
            for i, line in enumerate(_file_lines):
                if "========" in line:
                    _start_key = _file_lines[i + 1].strip().split(" ")[0]
                    if _start_key in self.items[self.dtype[0]]:
                        _type = self.dtype[0]
                        _items_list = self.items[_type]
                    elif _start_key in self.items[self.dtype[1]]:
                        _type = self.dtype[1]
                        _items_list = self.items[_type]
                    else:
                        return None
                    _read_flag = True
                    continue
                if _read_flag:
                    _line = line
                    if _line.count("*") == 1:
                        if _line.index("*") > 50:
                            _line = _line.split("*")
                            _line.insert(0, " ")
                        else:
                            _line = _line.split("*")
                    elif _line.count("*") == 2:
                        _line = _line.split("*")
                    elif "SPEC" in _line and "base2006" in _line:
                        _line = [line, _file_lines[i + 1]]
                        _read_flag = False
                    else:
                        _line = ["NR/RE", "NR/RE"]
                    for j, _l in enumerate(_line[:2]):
                        temp = re.findall(r" +\d+\.?\d*e?-?\d*?", _l)
                        _str = "NR/RE"
                        if len(temp) > 0:
                            _str = temp[-1].strip()
                            if _thread is None:
                                _thread = (self.thread[1] if temp[0].strip() > '1' else self.thread[0])
                        _scores_tune[self.tune[j]].append(_str)
                    if not _read_flag:
                        break
            if not _thread or not _type:
                print("线程数为%s,测试类型为%s!" % (_thread, _type))
                continue
            _items_key = _thread + "_" + _type
            score_dict = {}
            for k, v in _scores_tune.items():
                score_dict[k] = dict(zip(_items_list, v))
            ret_dict["items"][_items_key] = score_dict
        return ret_dict


class Speccpu2017(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_CPU17
        self.dtype = ["fp", "int"]
        self.items = {
            self.dtype[0]: {
                "rate": [
                    "503.bwaves_r", "507.cactuBSSN_r",
                    "508.namd_r", "510.parest_r",
                    "511.povray_r", "519.lbm_r",
                    "521.wrf_r", "526.blender_r",
                    "527.cam4_r", "538.imagick_r",
                    "544.nab_r", "549.fotonik3d_r",
                    "554.roms_r",
                    "SPECrate2017_fp"],
                "speed": [
                    "603.bwaves_s",
                    "607.cactuBSSN_s",
                    "619.lbm_s", "621.wrf_s",
                    "627.cam4_s", "628.pop2_s",
                    "638.imagick_s", "644.nab_s",
                    "649.fotonik3d_s", "654.roms_s",
                    "SPECspeed2017_fp"]},
            self.dtype[1]: {
                "rate": [
                    "500.perlbench_r", "502.gcc_r",
                    "505.mcf_r", "520.omnetpp_r",
                    "523.xalancbmk_r", "525.x264_r",
                    "531.deepsjeng_r", "541.leela_r",
                    "548.exchange2_r", "557.xz_r",
                    "SPECrate2017_int"],
                "speed": [
                    "600.perlbench_s", "602.gcc_s",
                    "605.mcf_s", "620.omnetpp_s",
                    "623.xalancbmk_s",
                    "625.x264_s",
                    "631.deepsjeng_s",
                    "641.leela_s",
                    "648.exchange2_s",
                    "657.xz_s",
                    "SPECspeed2017_int"]}}
        self.thread = ["单线程", "多线程"]
        self.tune = ["base", "peak"]

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name, "items": {}}
        ret_names_json = None
        with open(file, 'r') as f:
            try:
                ret_names_json = json.loads(f.read())
            except Exception as e:
                print("json 文件打开失败!", e)
                return None

        for _file in list(ret_names_json.values()):
            if not _file:
                continue
            _thread = None
            _read_flag = False
            _type_int_fp = None
            _type_rate_speed = None
            _file_lines = _file.split("\n")
            _scores_tune = []
            _scores_tune = {self.tune[0]: [], self.tune[1]: []}
            for i, line in enumerate(_file_lines):
                if "========" in line:
                    _read_flag = True
                    continue
                if _read_flag:
                    _line = line
                    if _line.count("*") == 1:
                        if _line.index("*") > 50:
                            _line = _line.split("*")
                            _line.insert(0, " ")
                        else:
                            _line = _line.split("*")
                    elif _line.count("*") == 2:
                        _line = _line.split("*")
                    elif all(key in line for key in ["2017", "base"]):
                        _regx = r"(?<=SPEC)[a-z]*|(?<=_)[a-z]*"
                        _flag = re.findall(_regx, _line)
                        _type_rate_speed = _flag[0]
                        _type_int_fp = _flag[1]
                        _line = [line, _file_lines[i + 1]]
                        _read_flag = False
                    else:
                        _line = ["NR/RE", "NR/RE"]
                    for j, _l in enumerate(_line[:2]):
                        temp = re.findall(r" +\d+\.?\d*e?-?\d*?", _l)
                        _str = ''
                        if len(temp) > 0:
                            _str = temp[-1].strip()
                            if not _thread:
                                _thread = (self.thread[1] if temp[0].strip() > '1' else self.thread[0])
                        else:
                            _str = "NR/RE"
                        _scores_tune[self.tune[j]].append(_str)
                    if not _read_flag:
                        break
            _score_key = "%s_%s_%s" % (_thread, _type_int_fp, _type_rate_speed)
            _items_list = self.items[_type_int_fp][_type_rate_speed]
            score_dict = {}
            for k, v in _scores_tune.items():
                score_dict[k] = dict(zip(_items_list, v))
            ret_dict["items"][_score_key] = score_dict
        return ret_dict


class Iozone(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_IOZONE
        self.items = {"block_size": "",
                      "rw_items": ["写测试（KB/s）", "重写测试（KB/s）", "读测试（KB/s）", "重读测试（KB/s）", "随机读测试（KB/s）", "随机写测试（KB/s）"]}

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name}
        with open(file, 'r') as f:
            lines = f.readlines()
        ret_dict['测试记录'] = []
        find_result = False
        for line in lines:
            if find_result == False:
                if line.strip()[0:2] == "kB":
                    find_result = True
            else:
                record = line.strip().split(' ')
                while '' in record:
                    record.remove('')
                ret_dict['测试记录'].append({
                    '文件大小': int(record[0]),
                    '块大小': int(record[1]),
                    '写测试（KB/s）': int(record[2]),
                    '重写测试（KB/s）': int(record[3]),
                    '读测试（KB/s）': int(record[4]),
                    '重读测试（KB/s）': int(record[5]),
                    '随机读测试（KB/s）': int(record[6]),
                    '随机写测试（KB/s）': int(record[7])})
                break
        return ret_dict


class Specjvm2008(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_JVM08
        self.items = ["compiler", "compress", "crypto", "derby", "mpegaudio", "scimark.large", "scimark.small", "serial", "startup", "sunflow", "xml",
                      "Noncompliant composite result"]
        self.tune = ["base", "peak"]

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name, "items": {}}
        _read_flag = False
        _items_list = self.items
        _tune = None
        _file_lines = []
        with open(file, 'r') as f:
            _file_lines = f.readlines()
        _score_list = []
        _score_dict = {}
        for line in _file_lines:
            _tmp = re.findall(r"base|peak", line, re.IGNORECASE)
            if _tmp:
                _tune = _tmp[0].lower()
                _read_flag = True
                continue
            if _read_flag:
                if self.items[-1] in line:
                    _items_list[-1] = _items_list[-1] + ":"
                    _read_flag = False
                regx = "|".join("(?<=%s)" % s for s in _items_list)
                regx = r"(%s)\s+[a-zA-Z0-9.]*" % regx
                temp = re.search(regx, line, re.IGNORECASE)
                if not temp:
                    continue
                _score_list.append(temp.group().strip())
                if not _read_flag:
                    break
        _score_dict = dict(zip(self.items, _score_list))
        ret_dict["items"][_tune] = _score_dict
        return ret_dict


class Lmbench(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_LMB
        self.items = {
            "Basic system parameters": ["Mhz", "tlb pages",
                                        "cache line bytes",
                                        "mem par", "scal load"],
            "Processor": ["Mhz", "null call", "null I/O", "stat",
                          "open close", "slct TCP", "sig inst",
                          "sig hndl", "fork proc", "exec proc",
                          "sh proc"],
            "Basic integer operations": ["intgr bit", "intgr add",
                                         "intgr mul", "intgr div",
                                         "intgr mod"],
            "Basic uint64 operations": ["int64 bit", "int64 add",
                                        "int64 mul", "int64 div",
                                        "int64 mod"],
            "Basic float operations": ["float add", "float mul",
                                       "float div", "float bogo"],
            "Basic double operations": ["double add", "double mul",
                                        "double div", "double bogo"],
            "Context switching": ["2p/0K", "2p/16K",
                                  "2p/64K", "8p/16K",
                                  "8p/64K", "16p/16K",
                                  "16p/64K"],
            "*Local* Communication latencies": ["2p/0K", "Pipe",
                                                "AF UNIX", "UDP",
                                                "RPC/UDP", "TCP",
                                                "RPC/TCP", "TCP conn"
                                                ],
            "File & VM system latencies in microseconds":
                ["0K File create", "0K File delete",
                 "10K File create", "10K File delete",
                 "Mmap Latency", "Prot Fault", "Page Fault",
                 "100fd selct",
                 ],
            "*Local* Communication bandwidths in MB/s - bigger is better":
                ["Pipe", "AF UNIX", "TCP", "File reread", "Mmap reread",
                 "Bcopy(libc)", "Bcopy(hand)", "Mem read", "Mem write"],
            "Memory latencies in nanoseconds": ["Mhz", "L1 $",
                                                "L2 $", "Main mem",
                                                "Rand mem"]
        }

    def parse_target_len(self, t_line):
        target_lens = list()
        if not t_line:
            return target_lens

        raw_target_lens = [len(x) for x in t_line.strip("\n").split(' ')]
        offset = 0
        for i in raw_target_lens:
            if i == 0:
                offset += 1
                continue
            target_lens.append(offset + i)
            offset = 0
        return target_lens

    def parse_data(self, data, target_lens):
        result_data = list()
        if not data or not target_lens:
            return result_data

        start = 0
        for i in target_lens:

            if start == 0:
                result = str(data[start: start + i])
                start += i
            else:
                result = str(data[start: start + i + 1])
                start += i + 1
            result = result.strip('\n .')
            if result.endswith("K") or result.endswith("k"):
                temp = re.search(r'\d+\.?\d*', result).group()
                result = str(float(temp) * 1000)
            result_data.append(result)
        return result_data

    def ret_to_dict(self, file):
        ret_dict = {"tool_name": self.tool_name}
        with open(file, 'r') as f:
            file_lines = f.readlines()
        _scores = []
        n = -2000
        for line in file_lines:
            if n < 0:
                for keywords in self.items.keys():
                    if keywords in line:
                        if keywords == "Basic system parameters":
                            n = 0
                        else:
                            n = 1
                        break
            if n == 5:
                target_line = "" + line  # type: str
                _scores_temp = list()
            if n >= 6 and not line.isspace() and 'make' not in line:
                data_line = line
                _score_temp = self.parse_data(
                    data_line, self.parse_target_len(target_line))
                if keywords == "Basic system parameters":
                    _scores_temp.append(_score_temp[3:])
                else:
                    _scores_temp.append(_score_temp[2:])
            if n >= 6 and (line.isspace() or line == file_lines[-1]):
                test_num = len(_scores_temp)
                if len(_scores) == test_num:
                    for i, v in enumerate(_scores_temp):
                        _scores[i] += v
                        # _scores[i].extend[v]
                else:
                    for i, v in enumerate(_scores_temp):
                        _scores.append([])
                        _scores[i] = v
                n = -2000
            n += 1
        ret_dict["items"] = []
        for _score in _scores:
            mid_ret_dict = []
            for (key, value) in self.items.items():
                mid_ret_dict.append(
                    {key: dict(zip(value, _score[:len(value)]))})
                del _score[:len(value)]
            ret_dict["items"].append(mid_ret_dict)
        return ret_dict


class Stream(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_STREAM
        self.items = ["Array size", "Copy", "Scale", "Add", "Triad"]
        self.thread = ["单线程", "多线程"]

    def ret_to_dict(self, file: str):
        stream_result_str = None
        _single_result = None
        _multiple_result = None

        ret_dict = {"tool_name": self.tool_name}

        score_list = ['' for i in self.items]
        ret_dict[self.thread[0]] = dict(
            zip(self.items, score_list))
        ret_dict[self.thread[1]] = dict(
            zip(self.items, score_list))

        # 打印字典中的内容
        # print(ret_dict)
        # 读取单核测试结果和多核测试结果
        with open(file, 'r') as f:
            stream_result_str = f.read()
        if stream_result_str:
            stream_json = json.loads(stream_result_str)
            # print(stream_json['single'])
            # print(stream_json['multiple'])
            _single_result = stream_json['single']
            _multiple_result = stream_json['multiple']

            # 处理单核测试结果
            if (_single_result is not None and len(_single_result) > 0):
                for line in _single_result.split('\n'):
                    for k in self.items:
                        if k in line:
                            temp = re.findall(r"-?\d+\.?\d*e?-?\d*?", line)
                            if temp[0]:
                                ret_dict[self.thread[0]][k] = temp[0]
            else:
                print("stream 测试没有单核测试结果")

            # 处理多核测试结果
            if (_multiple_result is not None and len(_multiple_result) > 0):
                for line in _multiple_result.split('\n'):
                    for k in self.items:
                        if k in line:
                            temp = re.findall(r"-?\d+\.?\d*e?-?\d*?", line)
                            if temp[0]:
                                ret_dict[self.thread[1]][k] = temp[0]
            else:
                print("stream 测试没有多核测试结果")

            # print(ret_dict)
        if len(ret_dict.keys()) > 1:
            return ret_dict
        else:
            return None


class Netperf(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_NETPERF
        self.items = ["TCP_Stream", "UDP_Stream", "网络响应时间", "TCP_CRR", "TCP_RR", "UDP_RR"]

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name}
        ret_dict['测试记录'] = []
        with open(file, 'r') as f:
            lines = f.readlines()
            for i in [6, 13, 22, 28, 36, 44]:
                ret_dict['测试记录'].append(lines[i].strip().split(' ')[-1])
        return ret_dict


class Fio(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_FIO
        self.items = {"items": ["bs", "io", "iops", "bw"]}

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name}
        units = {"k": 1e3, "M": 1e6, "G": 1e9}
        _file_lines = None
        _rw = None
        with open(file, "r") as f:
            _file_lines = f.readlines()
        if not _file_lines:
            print("file is empty")
            return None
        _regx = r'(?<=rw=).[a-z_]*'
        _rw = re.findall(_regx, _file_lines[0])
        if len(_rw) > 0:
            _rw = _rw[0]
        else:
            print("Fio:rw not found")
            return None
        _regx = r'(?<=bs=\(R\)\s).[A-Z0-9_\.]*'
        _bs = re.findall(_regx, _file_lines[0])
        if len(_bs) > 0:
            _bs = _bs[0]
        else:
            print("Fio:bs not found")
            return None
        _read_flag = "read"
        _read_flag = _read_flag if _read_flag in _rw else "write"
        _flags_list = [_read_flag, "IOPS", "BW"]
        _iops = 0
        _bw = 0
        _io = 0
        for line in _file_lines[1:]:
            line = line.strip(" ")
            if all(_f in line for _f in _flags_list):
                _regx = r'(?<=IOPS=).*,'
                _iops = re.findall(_regx, line)[0][:-1]
                for unit in units:
                    if unit in _iops:
                        _iops = float(_iops.replace(unit, '')) * units[unit]
                        break
                _regx = r'(?<=BW=).*\)'
                _bw_io = re.findall(_regx, line)
                _bw_list = _bw_io[0].split(")")[0].split("(")
                _bw = _bw_list[0].strip(" ") + " (" + _bw_list[1] + ")"
                _io = _bw_io[0].split(")")[1].split("(")[1].split("/")[0]
                break
        ret_dict["rw"] = _rw
        ret_dict["items"] = dict(
            zip(self.items["items"], [_bs, _io, _iops, _bw]))
        return ret_dict


class Export(object):
    def __init__(self):
        self.env_dict = None
        self.ret_dict = None
        self.tool_name = None
        self.tool_cls = None

    @staticmethod
    def get_files(ret_path: str) -> list:
        files = []
        if os.path.isfile(ret_path):
            return [ret_path]
        try:
            files = [os.path.join(ret_path, file)
                     for file in os.listdir(ret_path)
                     if os.path.isfile(os.path.join(ret_path, file))]
        except Exception as e:
            print("列出文件失败!", e)
        return files

    @staticmethod
    def get_tool_cls(tool_name):
        """通过工具名实例化使用的类"""
        cls_dict = {v.__name__: v for v in BenchMark.__subclasses__()}
        match_names = difflib.get_close_matches(
            tool_name, list(cls_dict.keys()), 1)
        return cls_dict.get(match_names[0])()

    def ret_to_dict(self, tool_name: str, ret_path: str, cmd: str, argv: str) -> list:
        """结果解析转化为字典"""
        ret_dict = {}
        _tool_name = tool_name
        _ret_path = ret_path
        self.tool_cls = self.get_tool_cls(_tool_name)
        if self.tool_cls is None:
            print("未能实例化工具类!\n")
            return ret_dict
        self.tool_cls.value_cmd = cmd
        self.tool_cls.value_modify_args = argv
        self.tool_cls.tool_name = _tool_name
        return self.tool_cls.ret_to_dict(_ret_path)

    def rets_to_dict_list(self, tool_name: str, ret_path: str, cmd: str, argv: str) -> list:
        ret_dict_list = []
        for file in self.get_files(ret_path):
            ret_dict = self.ret_to_dict(tool_name, file, cmd, argv)
            if ret_dict is None:
                continue
            ret_dict_list.append(ret_dict)
        return ret_dict_list


support_tools = {'lmbench': TOOL_NAME_LMB, 'unixbench': TOOL_NAME_UB, 'speccpu2006': TOOL_NAME_CPU06,
                 'speccpu2017': TOOL_NAME_CPU17, 'iozone': TOOL_NAME_IOZONE, 'specjvm2008': TOOL_NAME_JVM08,
                 'stream': TOOL_NAME_STREAM, 'netperf': TOOL_NAME_NETPERF, 'fio': TOOL_NAME_FIO}


def constructParse():
    parser = argparse.ArgumentParser(description="Export benchmark raw results to excel format.")
    parser.add_argument('-n', '--name', choices=support_tools.keys(), help='benchmark name.', type=str)
    parser.add_argument('-f', '--file', help='absolute path of benchmark raw result.', type=str)
    parser.add_argument('-o', '--output', help='the dir where we export excel to.', default=os.getcwd(), type=str)
    return parser
