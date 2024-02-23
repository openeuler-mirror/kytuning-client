#!/usr/bin/python3
# 功能：从环境/测试结果json文件导出到excel
# 依赖库：openpyxl

__all__ = ['ExportXlsx']
import os
import re
import json
import difflib
import argparse
from base64 import b64decode
from openpyxl import Workbook, load_workbook, utils
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Alignment
from openpyxl.styles import Font, PatternFill, Side, Border

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

        self.alignment_center = Alignment(
            horizontal='center', vertical='center', wrapText=True)
        self.alignment_left = Alignment(
            horizontal='left', vertical='center', wrapText=True)
        self.ret_col_1_width = 30
        self.ret_col_2_width = 20
        self.ret_col_data_width = 15

        self.ret_row_1_height = 50

        # 起始行列
        self.row_point_start = 1
        self.col_point_start = 1

        # 初始化行与列的高度和宽度,可在各个子类中覆盖.
        self.cols_width = [self.ret_col_1_width]
        self.rows_height = [
            25,                    # 开始行
            25,                    # 命令行
            self.ret_row_1_height] # 参数行

        # excel_style
        thin = Side(border_style="thin", color="000000")
        self.border_thin = Border(
            top=thin, left=thin, right=thin, bottom=thin)
        self.color_title = PatternFill("solid", fgColor="CC99FF")
        self.font_title = Font(name="宋体", size=20, bold=True, color="993300")

        self.color_cmd = PatternFill("solid", fgColor="CCFFFF")
        self.font_cmd = Font(name="宋体", size=13, bold=True, color="000000")

        self.color_col_top = PatternFill("solid", fgColor="99CCFF")
        self.font_col_top = Font(name="宋体", size=18, color="000000")

        self.color_item_1 = PatternFill("solid", fgColor="FFCC99")
        self.font_item_1 = Font(name="宋体", size=13, color="000000")
        self.color_item_2 = PatternFill("solid", fgColor="CCFFCC")
        self.font_item_2 = Font(name="宋体", size=11, color="000000")

        self.color_data = PatternFill()
        self.font_data = Font(name="宋体")

    @property
    def row_data_start(self):
        return self.row_point_start + len(self.rows_height)

    @property
    def col_data_start(self):
        return self.col_point_start + len(self.cols_width)

    def set_cell_style(
        self, sheet, row_idx, col_idx, value,
            alg, fill=PatternFill(), font=Font(name="宋体")):
        cell = sheet.cell(row_idx, col_idx, value)
        cell.border = self.border_thin
        cell.alignment = alg
        cell.fill = fill
        cell.font = font

    def merge_col_cell(
            self, worksheet: Worksheet, N: str, row_A: int, row_B: int):
        if row_B - row_A > 0:
            alignment = Alignment(horizontal='center', vertical='center')
            merge_row = str(N) + str(row_A) + ':' + str(N) + str(row_B)
            worksheet.merge_cells(merge_row)
            merge_row = str(N)+str(row_A)
            worksheet[merge_row].alignment = alignment

    def unmerge_col_cell(
            self, worksheet: Worksheet, N: str, row_A: int, row_B: int):
        if row_B - row_A > 0:
            merge_row = str(N) + str(row_A) + ':' + str(N) + str(row_B)
            worksheet.unmerge_cells(merge_row)

    def merge_col_cell_by_value(self, sheet: Worksheet, N: str, row_A: int, row_B: int, value = None):
        if row_B - row_A > 0:
            merge_row = 0
            if row_A > self.row_point_start and value is not None:
                for i in range(self.row_point_start, row_A):
                    cval = sheet.cell(row_A - i, utils.column_index_from_string(N)).value
                    if cval is None:
                        continue
                    if cval == value:
                        merge_row = i
                    break
                if merge_row > 0:
                    self.unmerge_col_cell(sheet, N, row_A - merge_row, row_A - 1)
            self.merge_col_cell(sheet, N, row_A - merge_row, row_B)

    def merge_row_cell(
            self, worksheet: Worksheet, row_N: int, col_A: int, col_B: int):
        if col_B - col_A > 0:
            col_A = utils.get_column_letter(col_A)
            col_B = utils.get_column_letter(col_B)
            alignment = Alignment(horizontal='center', vertical='center')
            merge_row = str(col_A) + str(row_N) + ':' + str(col_B) + str(row_N)
            worksheet.merge_cells(merge_row)
            merge_row = str(col_A)+str(row_N)
            worksheet[merge_row].alignment = alignment

    def max_column_by_rows(self, sheet: Worksheet, min_row = None, max_row = None):
        if min_row is None and max_row is None:
            return sheet.max_column

        rows_vcount = []
        min_row = min_row or self.row_point_start
        max_row = max_row or sheet.max_row
        for row in sheet.iter_rows(min_row = min_row, max_row = max_row, values_only = True):
            row_vcount = len(row)
            for idx in range(row_vcount, self.col_point_start - 1, -1):
                if row[idx - 1] is None:
                    row_vcount -= 1
                else:
                    break
            rows_vcount.append(row_vcount)
        return max(tuple(rows_vcount)) if len(rows_vcount) > 0 else sheet.max_column

    def find_row_point(self, sheet: Worksheet, data: dict):
        if sheet.max_row >= self.row_data_start:
            col_values = [None for i in range(0, len(data))]
            for row in sheet.iter_rows(min_row = self.row_data_start):
                for idx in range(0, len(data)):
                    if row[self.col_point_start - 1 + idx].value is not None:
                        col_values[idx] = row[self.col_point_start - 1 + idx].value
                for idx, _v in enumerate(data.values()):
                    if col_values[idx] != _v:
                        break
                else:
                    return row[self.col_point_start - 1].row
        return sheet.max_row + 1

    def find_col_point(self, sheet: Worksheet, row: int):
        if sheet.max_column >= self.col_data_start:
            for col in sheet.iter_cols(min_col = self.col_data_start):
                if col[row - 1].value is None:
                    if col[self.row_point_start - 1 + 2].value is None or col[self.row_point_start - 1 + 2].value == self.value_modify_args:
                        return col[self.row_point_start].column
        return sheet.max_column + 1

    def set_col_items(self, sheet: Worksheet):
        point_row = self.row_point_start
        point_col = self.col_point_start
        cols_num = len(self.cols_width)
        # 开始
        self.set_cell_style(sheet, point_row, point_col, self.tool_name,
                            self.alignment_center, self.color_title, self.font_title)
        self.merge_row_cell(sheet, point_row, point_col, point_col + cols_num - 1)
        # 执行命令
        point_row += 1
        self.set_cell_style(sheet, point_row, point_col, self.text_cmd,
                            self.alignment_center, self.color_cmd, self.font_cmd)
        self.merge_row_cell(sheet, point_row, point_col, point_col + cols_num - 1)
        # 修改参数
        point_row += 1
        self.set_cell_style(sheet, point_row, point_col, self.text_modify_args,
                            self.alignment_center, self.color_cmd, self.font_cmd)
        self.merge_row_cell(sheet, point_row, point_col, point_col + cols_num - 1)

        for idx, wth in enumerate(self.cols_width):
            sheet.column_dimensions[utils.get_column_letter(idx + self.col_point_start)].width = wth

        for idx, hgh in enumerate(self.rows_height):
            sheet.row_dimensions[idx + self.row_point_start].height = hgh
        pass

    def set_col_title(self, sheet: Worksheet, col_point: int):
        if col_point > sheet.max_column:
            sheet.column_dimensions[utils.get_column_letter(col_point)].width = self.ret_col_data_width
            self.set_cell_style(sheet, self.row_point_start, col_point, self.tool_name + '#' + str(col_point - 2),
                                self.alignment_center, self.color_col_top, self.font_col_top)
            self.set_cell_style(sheet, self.row_point_start + 1, col_point, self.value_cmd,
                                self.alignment_center, self.color_data, self.font_data)
            self.set_cell_style(sheet, self.row_point_start + 2, col_point, self.value_modify_args,
                                self.alignment_center, self.color_data, self.font_data)
        else:
            if sheet.cell(self.row_point_start + 1, col_point).value != self.value_cmd:
                self.set_cell_style(sheet, self.row_point_start + 1, col_point, sheet.cell(self.row_point_start + 1, col_point).value + "\n" + self.value_cmd,
                                self.alignment_center, self.color_data, self.font_data)
        pass

    def set_row_header(self, sheet: Worksheet, row_point: int, ret_dict):
        if row_point > sheet.max_row:
            pass
            # self.set_cell_style(sheet, row_point, 1, ret_dict['rw'], self.alignment_center, self.color_item_1, self.font_item_1)
            # for i, _l in enumerate(self.items["items"]):
            #     self.set_cell_style(sheet, row_point + i, 2, _l, self.alignment_center, self.color_item_2, self.font_item_2)
            # self.merge_col_cell(sheet, "A", row_point, row_point + len(self.items["items"]) - 1)
        pass

    def ret_to_dict(self, file: str): ...

    def env_dict_to_excel(self, sheet: Worksheet, env_dict: dict):
        if not env_dict:
            return
        text_sheet_title = "性能测试环境统计表"
        _env_dict = env_dict
        index_start = 1
        self.set_cell_style(sheet, index_start, index_start,
                            text_sheet_title, self.alignment_center,
                            self.color_title, self.font_title)
        sheet.merge_cells('A1:%s1' % (
            utils.get_column_letter(3+1)))  # +1是包含字典中值的那一列
        sheet.column_dimensions["A"].width = 15
        sheet.column_dimensions["B"].width = 15
        sheet.column_dimensions["C"].width = 15
        sheet.column_dimensions["D"].width = 50
        sheet.row_dimensions[1].height = 30

        base64_list = ["sysctl", "sysconf",
                       "systemctlinfo", "driverinfo", "rpmlist", "ipclist"]

        row_start_idx = 5
        _row_up = 0
        _row = 1
        A_names = list(_env_dict["envinfo"].keys())
        A_names_len = len(A_names)
        for A_i in range(A_names_len):     # 遍历第一列中的内容
            self.set_cell_style(
                sheet, _row+row_start_idx,
                1,  A_names[A_i], self.alignment_center,
                self.color_title, self.font_title)  # 填充第一列中的内容  'hwinfo'
            _row_A = _row
            # print(type(env_dict["envinfo"][A_names[A_i]]))
            if type(_env_dict["envinfo"][A_names[A_i]]) != str:
                key_names = list(_env_dict["envinfo"][A_names[A_i]].keys())
                keys_len = len(key_names)
                for i in range(keys_len):   # 遍历第二列中的内容
                    # print(key_names[i])
                    self.set_cell_style(
                        sheet, _row + row_start_idx,
                        2, key_names[i], self.alignment_center,
                        self.color_item_1, self.font_item_1)   # 填充第二列中的内容
                    value_type = type(
                        _env_dict["envinfo"][A_names[A_i]][key_names[i]])
                    if value_type == str:
                        cell_str = _env_dict["envinfo"][A_names[A_i]
                                                        ][key_names[i]]
                        self.set_cell_style(
                            sheet, _row+row_start_idx, 4,
                            cell_str,
                            self.alignment_left,
                            self.color_data, self.font_data)
                        _row = _row + 1
                    elif value_type == dict:
                        dict_keys_name = list(
                            _env_dict["envinfo"][A_names[A_i]
                                                 ][key_names[i]].keys())
                        dict_keys_len = len(dict_keys_name)
                        _row_up = _row
                        for j in range(dict_keys_len):
                            self.set_cell_style(
                                sheet, _row+row_start_idx, 3,
                                dict_keys_name[j], self.alignment_center,
                                self.color_item_2, self.font_item_2)  # 填充第三列
                            dict_keys_type = type(
                                _env_dict["envinfo"][A_names[A_i]
                                                     ][key_names[i]
                                                       ][dict_keys_name[j]])
                            if dict_keys_type == str:
                                cell_str = _env_dict["envinfo"
                                                     ][A_names[A_i]
                                                       ][key_names[i]
                                                         ][dict_keys_name[j]]
                                if any(dict_keys_name[j]
                                       in s for s in base64_list):
                                    cell_str = b64decode(
                                        cell_str).decode("ascii")
                                col_n = 4
                                while True:
                                    if len(cell_str) > 8100:
                                        _cell_str = cell_str[:8100]
                                        if not _cell_str.endswith('\n'):
                                            _line_end = _cell_str.rfind('\n')
                                            _cell_str = cell_str[:_line_end]
                                        cell_str = cell_str[len(_cell_str):]

                                        self.set_cell_style(
                                            sheet, _row+row_start_idx, col_n,
                                            _cell_str.encode("ascii"),
                                            self.alignment_left,
                                            self.color_data, self.font_data)
                                        col_n += 1
                                        sheet.column_dimensions[
                                            utils.get_column_letter(
                                                col_n)].width = 50
                                    else:
                                        self.set_cell_style(
                                            sheet, _row+row_start_idx, col_n,
                                            cell_str.encode("ascii"),
                                            self.alignment_left,
                                            self.color_data, self.font_data)
                                        break
                            _row = _row + 1
                        # 合并第二列中的单元格
                        self.merge_col_cell(
                            sheet, 'B',
                            _row_up+row_start_idx, _row-1+row_start_idx)
                    elif value_type == list:
                        _row_up = _row
                        for list_l in _env_dict["envinfo"][A_names[A_i]
                                                           ][key_names[i]]:
                            if type(list_l) == str:  # memType
                                # print(list_l)
                                self.set_cell_style(
                                    sheet, _row+row_start_idx, 4, list_l,
                                    self.alignment_left,
                                    self.color_data, self.font_data)
                                _row = _row + 1
                            elif type(list_l) == dict:  # disk
                                list_key_names = list(list_l.keys())
                                for list_key_name in list_key_names:
                                    # print(list_key_name)
                                    # 填充第三列中的内容
                                    self.set_cell_style(
                                        sheet, _row+row_start_idx, 3,
                                        list_key_name,
                                        self.alignment_center,
                                        self.color_item_2, self.font_item_2)
                                    if type(list_l[list_key_name]) == str:
                                        self.set_cell_style(
                                            sheet, _row + row_start_idx, 4,
                                            list_l[list_key_name],
                                            self.alignment_left,
                                            self.color_data, self.font_data)
                                    _row = _row + 1
                        # 合并第二列中的单元格
                        self.merge_col_cell(
                            sheet, 'B',
                            _row_up+row_start_idx, _row-1+row_start_idx)
                # 合并第一列中的单元格
                self.merge_col_cell(sheet, 'A',
                                    _row_A+row_start_idx, _row-1+row_start_idx)
            else:
                self.set_cell_style(
                    sheet, _row +
                    row_start_idx, 4, _env_dict["envinfo"][A_names[A_i]],
                    self.alignment_left,
                    self.color_data, self.font_data)

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict): ...


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
        self.xlsx_col = self.thread
        self.cpu_num_flag = "CPUs in system"
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
        ret_dict[self.thread[0]] = dict(
            zip(self.items, score_list))
        ret_dict[self.thread[1]] = dict(
            zip(self.items, score_list))
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

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        sheet = None
        if self.tool_name in workbook.sheetnames:  # 已存在sheet
            sheet = workbook[self.tool_name]
        else:   # 不存在sheet
            sheet = workbook.create_sheet(self.tool_name)
            self.set_col_items(sheet)

        for tune in self.thread:
            if tune not in ret_dict.keys():
                continue
            row_point = self.find_row_point(sheet, {"tune": tune})
            self.set_row_header(sheet, row_point, {"tune": tune})

            col_point = self.find_col_point(sheet, row_point)
            self.set_col_title(sheet, col_point)

            for _, _v in ret_dict[tune].items():
                self.set_cell_style(sheet, row_point, col_point, _v.strip(" "),
                                    self.alignment_center, self.color_data, self.font_data)
                row_point += 1


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
        self.cols_width = [10, 10, self.ret_col_2_width]

    def set_row_header(self, sheet: Worksheet, row_point: int, data: dict):
        if row_point > sheet.max_row:
            self.set_cell_style(sheet, row_point, self.col_point_start, data["thread"], self.alignment_center, self.color_item_1, self.font_item_1)
            self.set_cell_style(sheet, row_point, self.col_point_start + 1, data["type"], self.alignment_center, self.color_item_1, self.font_item_1)
            for i, _l in enumerate(self.items[data["type"]]):
                self.set_cell_style(sheet, row_point + i, self.col_point_start + 2, _l, self.alignment_left, self.color_item_2, self.font_item_2)

            self.merge_col_cell_by_value(sheet, utils.get_column_letter(self.col_point_start + 1), row_point, row_point + len(self.items[data["type"]]) - 1, data["type"])
            self.merge_col_cell_by_value(sheet, utils.get_column_letter(self.col_point_start), row_point, row_point + len(self.items[data["type"]]) - 1, data["thread"])
        pass

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
                    _start_key = _file_lines[i+1].strip().split(" ")[0]
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
                        _line = [line, _file_lines[i+1]]
                        _read_flag = False
                    else:
                        _line = ["NR/RE", "NR/RE"]
                    for j, _l in enumerate(_line[:2]):
                        temp = re.findall(r" +\d+\.?\d*e?-?\d*?", _l)
                        _str = "NR/RE"
                        if len(temp) > 0:
                            _str = temp[-1].strip()
                            _thread = (
                                self.thread[1] if temp[0].strip() > '1' else
                                self.thread[0])
                        _scores_tune[self.tune[j]].append(_str)
                    if not _read_flag:
                        break
            if not _thread or not _type:
                print("线程数为%s,测试类型为%s!" % (_thread, _type))
                return None
            _items_key = _thread+"_"+_type
            score_dict = {}
            for k, v in _scores_tune.items():
                score_dict[k] = dict(zip(_items_list, v))
            ret_dict["items"][_items_key] = score_dict
        return ret_dict

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        is_new = True
        idx_col = self.index_start
        index_start_row = self.index_start
        for k, v in ret_dict["items"].items():
            for _k, _v in v.items():
                shee_name = "%s(%s)" % (self.tool_name, _k)

                _thread = k.split("_")[0]
                _dtype = k.split("_")[1]
                idx_start_items = 0
                if _thread == self.thread[0]:
                    if _dtype == self.dtype[0]:  # 单线程 fp
                        idx_start_items = index_start_row+3
                    else:                                   # 单线程 int
                        idx_start_items = 25  # 根据模板固定，也可以根据self.items计算
                elif _thread == self.thread[1]:
                    if _dtype == self.dtype[0]:  # 多线程fp
                        idx_start_items = 41
                    else:                                   # 多线程int
                        idx_start_items = 62
                sheet = None
                if shee_name in workbook.sheetnames:  # 已存在sheet
                    sheet = workbook[shee_name]
                else:   # 不存在sheet
                    sheet = workbook.create_sheet(shee_name)
                    self.set_col_items(sheet, _k)
                if is_new:
                    idx_col = sheet.max_column + 1
                    is_new = False
                # 列头
                sheet.column_dimensions[utils.get_column_letter(
                    idx_col)].width = self.ret_col_data_width
                self.set_cell_style(
                    sheet, idx_start_items-3, idx_col,
                    self.tool_name + '#'+str(idx_col-1),
                    self.alignment_center, self.color_col_top,
                    self.font_col_top)
                if self.value_cmd:
                    self.set_cell_style(
                        sheet, idx_start_items-2, idx_col,
                        self.value_cmd,
                        self.alignment_center, self.color_data, self.font_data)
                if self.value_modify_args:
                    self.set_cell_style(
                        sheet, idx_start_items-1, idx_col,
                        self.value_modify_args,
                        self.alignment_center, self.color_data, self.font_data)

                for i, (_, __v) in enumerate(_v.items()):
                    self.set_cell_style(
                        sheet, idx_start_items+i,
                        idx_col, __v, self.alignment_center)
        return True


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
        self.tune = ["base", "paek"]

    def set_col_items(self, sheet: Worksheet, tune: str):
        text_cmd = self.text_cmd
        text_modify_args = self.text_modify_args
        point_row = 1
        sheet.column_dimensions["A"].width = self.ret_col_2_width
        # 单线程fp开始
        self.set_cell_style(
            sheet, point_row, 1, "单线程FP", self.alignment_center,
            self.color_title, self.font_title)
        point_row += 1
        # 执行命令
        self.set_cell_style(
            sheet, point_row, 1, text_cmd, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        # 修改参数
        sheet.row_dimensions[point_row].height = self.ret_row_1_height
        self.set_cell_style(
            sheet, point_row, 1, text_modify_args, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        for v in self.items[self.dtype[0]].values():
            for i, _v in enumerate(v):
                _v = _v+"_"+tune if i == (len(v)-1) else _v
                self.set_cell_style(
                    sheet, point_row, 1, _v, self.alignment_left,
                    self.color_item_1, self.font_item_1)
                point_row += 1
        # 单线程int开始
        self.set_cell_style(
            sheet, point_row, 1, "单线程INT", self.alignment_center,
            self.color_title, self.font_title)
        point_row += 1
        # 执行命令
        self.set_cell_style(
            sheet, point_row, 1, text_cmd, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        # 修改参数
        sheet.row_dimensions[point_row].height = self.ret_row_1_height
        self.set_cell_style(
            sheet, point_row, 1, text_modify_args, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        for v in self.items[self.dtype[1]].values():
            for i, _v in enumerate(v):
                _v = _v+"_"+tune if i == (len(v) - 1) else _v
                self.set_cell_style(
                    sheet, point_row, 1, _v, self.alignment_left,
                    self.color_item_1, self.font_item_1)
                point_row += 1
        # 多线程fp开始
        self.set_cell_style(
            sheet, point_row, 1, "多线程FP", self.alignment_center,
            self.color_title, self.font_title)
        point_row += 1
        # 执行命令
        self.set_cell_style(
            sheet, point_row, 1, text_cmd, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        # 修改参数
        sheet.row_dimensions[point_row].height = self.ret_row_1_height
        self.set_cell_style(
            sheet, point_row, 1, text_modify_args, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        for v in self.items[self.dtype[0]].values():
            for i, _v in enumerate(v):
                _v = _v+"_"+tune if i == (len(v) - 1) else _v
                self.set_cell_style(
                    sheet, point_row, 1, _v, self.alignment_left,
                    self.color_item_1, self.font_item_1)
                point_row += 1
        # 多线程int开始
        self.set_cell_style(
            sheet, point_row, 1, "多线程INT", self.alignment_center,
            self.color_title, self.font_title)
        point_row += 1
        # 执行命令
        self.set_cell_style(
            sheet, point_row, 1, text_cmd, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        # 修改参数
        sheet.row_dimensions[point_row].height = self.ret_row_1_height
        self.set_cell_style(
            sheet, point_row, 1, text_modify_args, self.alignment_center,
            self.color_cmd, self.font_cmd)
        point_row += 1
        for v in self.items[self.dtype[1]].values():
            for i, _v in enumerate(v):
                _v = _v+"_"+tune if i == (len(v) - 1) else _v
                self.set_cell_style(
                    sheet, point_row, 1, _v, self.alignment_left,
                    self.color_item_1, self.font_item_1)
                point_row += 1

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
                    elif all(key in line for key in [
                            "2017", "base"]):
                        _regx = r"(?<=SPEC)[a-z]*|(?<=_)[a-z]*"
                        _flag = re.findall(_regx, _line)
                        _type_rate_speed = _flag[0]
                        _type_int_fp = _flag[1]
                        _line = [line, _file_lines[i+1]]
                        _read_flag = False
                    else:
                        _line = ["NR/RE", "NR/RE"]
                    for j, _l in enumerate(_line[:2]):
                        temp = re.findall(r" +\d+\.?\d*e?-?\d*?", _l)
                        _str = ''
                        if len(temp) > 0:
                            _str = temp[-1].strip()
                            _thread = (
                                self.thread[1] if temp[0].strip() > '1' else
                                self.thread[0])
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

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        is_new = True
        idx_col = self.index_start
        index_start_row = self.index_start
        for k, v in ret_dict["items"].items():
            for _k, _v in v.items():
                _thread = k.split("_")[0]
                _dtype = k.split("_")[1]
                _tune = k.split("_")[2]
                idx_start_items = 0
                if _thread == self.thread[0]:
                    if _dtype == self.dtype[0]:  # 单线程 fp
                        idx_start_items = index_start_row+3
                    else:                                   # 单线程 int
                        idx_start_items = 32  # 根据模板固定，也可以根据self.items计算
                elif _thread == self.thread[1]:
                    if _dtype == self.dtype[0]:  # 多线程fp
                        idx_start_items = 57
                    else:                                   # 多线程int
                        idx_start_items = 85
                if _tune == "speed":
                    idx_start_items += len(self.items[_dtype]["rate"])

                sheet = None
                shee_name = "%s(%s)" % (self.tool_name, _k)
                if shee_name in workbook.sheetnames:  # 已存在sheet
                    sheet = workbook[shee_name]
                else:   # 不存在sheet
                    sheet = workbook.create_sheet(shee_name)
                    self.set_col_items(sheet, _k)
                if is_new:
                    idx_col = sheet.max_column + 1
                    is_new = False
                # 列头
                if _tune == "rate":
                    sheet.column_dimensions[utils.get_column_letter(
                        idx_col)].width = self.ret_col_data_width
                    self.set_cell_style(
                        sheet, idx_start_items-3, idx_col,
                        self.tool_name + '#'+str(idx_col-1),
                        self.alignment_center, self.color_col_top,
                        self.font_col_top)
                    if self.value_cmd:
                        self.set_cell_style(
                            sheet, idx_start_items-2, idx_col,
                            self.value_cmd,
                            self.alignment_center, self.color_data, self.font_data)
                    if self.value_modify_args:
                        self.set_cell_style(
                            sheet, idx_start_items-1, idx_col,
                            self.value_modify_args,
                            self.alignment_center, self.color_data, self.font_data)

                for i, (_, __v) in enumerate(_v.items()):
                    self.set_cell_style(
                        sheet, idx_start_items+i,
                        idx_col, __v, self.alignment_center)
        return True


class Iozone(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_IOZONE
        self.items = {
            "block_size": "",
            "rw_items": ["写测试（KB/s）", "重写测试（KB/s）", "读测试（KB/s）",
                         "重读测试（KB/s）", "随机读测试（KB/s）", "随机写测试（KB/s）"]}
        self.color_title = PatternFill()
        self.font_title = Font(name="DejaVu Sans", size=20,
                               bold=True, color="993366")
        self.color_cmd = PatternFill()
        self.font_cmd = Font(name="Linrial", size=18,
                             bold=True, color="FF00FF")
        self.color_cmd_value = PatternFill("solid", fgColor="DBDBDB")
        self.font_cmd_value = Font(name="宋体", size=11)
        self.color_item = [PatternFill(
            "solid", fgColor="FFC000"), PatternFill("solid", fgColor="C6E0B4")]
        self.font_item = [Font(name="宋体", size=14, bold=True, color="993366"), Font(
            name="宋体", size=14, bold=True, color="993366")]
        self.color_fsize = [PatternFill(
            "solid", fgColor="AEAAAA"), PatternFill("solid", fgColor="BDD7EE")]
        self.font_fsize = [Font(name="宋体", size=12), Font(name="宋体", size=12)]
        self.color_data = [PatternFill(
            "solid", fgColor="A9D08E"), PatternFill("solid", fgColor="FFE699")]
        self.font_data = [Font(name="宋体", size=11), Font(name="宋体", size=11)]

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name}
        with open(file, 'r') as f:
            lines = f.readlines()
        ret_dict['测试记录'] = []
        for line in lines[28:-2]:
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
        return ret_dict

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        record_count = len(ret_dict['测试记录'])
        item_count = len(self.items['rw_items'])

        if ret_dict['tool_name'] in workbook.sheetnames:
            sheet = workbook[ret_dict['tool_name']]
        else:
            sheet = workbook.create_sheet(ret_dict['tool_name'])
            sheet.row_dimensions[1].height = 38
            sheet.row_dimensions[2].height = 29
            sheet.row_dimensions[3].height = 29
            for i in range(4, 4 + record_count * item_count):
                sheet.row_dimensions[i].height = 25
            sheet.column_dimensions['A'].width = 9.75
            sheet.column_dimensions['B'].width = 9.75
            sheet.merge_cells('A1:B1')
            sheet.merge_cells('A2:B2')
            sheet.merge_cells('A3:B3')
            self.set_cell_style(
                sheet, 1, 1, ret_dict['tool_name'], self.alignment_center, self.color_title, self.font_title)
            self.set_cell_style(sheet, 2, 1, self.text_cmd,
                                self.alignment_center, self.color_cmd, self.font_cmd)
            self.set_cell_style(sheet, 3, 1, self.text_modify_args,
                                self.alignment_center, self.color_cmd, self.font_cmd)
            for i in range(item_count):
                item_cell_start_row = 4 + i * record_count
                self.merge_col_cell(
                    sheet, 'A', item_cell_start_row, item_cell_start_row + record_count - 1)
                self.set_cell_style(sheet, item_cell_start_row, 1,
                                    self.items['rw_items'][i], self.alignment_center, self.color_item[i % 2], self.font_item[i % 2])
                for j in range(record_count):
                    self.set_cell_style(sheet, item_cell_start_row + j, 2,
                                        ret_dict['测试记录'][j]['文件大小'], self.alignment_center, self.color_fsize[i % 2], self.font_fsize[i % 2])

        column_index = len(sheet[1]) + 1
        sheet.column_dimensions[chr(ord('A')+column_index-1)].width = 18.25
        self.set_cell_style(sheet, 1, column_index, 'iozone#' + str(column_index-2),
                            self.alignment_left, self.color_col_top, self.font_col_top)
        self.set_cell_style(sheet, 2, column_index, self.value_cmd,
                            self.alignment_center, self.color_cmd_value, self.font_cmd_value)
        self.set_cell_style(sheet, 3, column_index, self.value_modify_args,
                            self.alignment_center, self.color_cmd_value, self.font_cmd_value)

        for i in range(item_count):
            item_cell_start_row = 4 + i * record_count
            for j in range(record_count):
                self.set_cell_style(sheet,
                                    item_cell_start_row + j,
                                    column_index,
                                    ret_dict['测试记录'][j][self.items['rw_items'][i]],
                                    self.alignment_center,
                                    self.color_data[i % 2], self.font_data[i % 2])

        return True


class Specjvm2008(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_JVM08
        self.items = ["compiler", "compress", "crypto",
                      "derby", "mpegaudio", "scimark.large",
                      "scimark.small", "serial", "startup",
                      "sunflow", "xml",
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
                    _items_list[-1] = _items_list[-1]+":"
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

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        for k, v in ret_dict["items"].items():
            point_row = 1
            point_col = 1
            _tune = k
            shee_name = "%s(%s)" % (self.tool_name, _tune)
            if shee_name in workbook.sheetnames:  # 已存在sheet
                sheet = workbook[shee_name]
                point_col = sheet.max_column + 1
            else:   # 不存在sheet
                sheet = workbook.create_sheet(shee_name)
                # 第一行,列
                sheet.column_dimensions[utils.get_column_letter(
                    point_col)].width = self.ret_col_1_width
                self.set_cell_style(
                    sheet, point_row, point_col, _tune.title(),
                    self.alignment_center, self.color_title,
                    self.font_title)
                point_row += 1
                # 执行命令
                self.set_cell_style(
                    sheet, point_row, point_col, self.text_cmd,
                    self.alignment_center, self.color_cmd,
                    self.font_cmd)
                point_row += 1
                # 修改参数
                sheet.row_dimensions[point_row].height = 50
                self.set_cell_style(
                    sheet, point_row, point_col, self.text_modify_args,
                    self.alignment_center, self.color_cmd,
                    self.font_cmd)
                point_row += 1
                for i, _v in enumerate(self.items):
                    self.set_cell_style(
                        sheet, point_row+i, point_col, _v,
                        self.alignment_center, self.color_item_1,
                        self.font_item_1)
                point_col += 1
            # 填充列头
            point_row = 1
            sheet.column_dimensions[utils.get_column_letter(
                point_col)].width = self.ret_col_data_width
            self.set_cell_style(
                sheet, point_row, point_col,
                self.tool_name + '#'+str(point_col-1),
                self.alignment_center, self.color_col_top, self.font_col_top)
            point_row += 1
            if self.value_cmd:
                self.set_cell_style(
                    sheet, point_row, point_col,
                    self.value_cmd,
                    self.alignment_center, self.color_data, self.font_data)
            point_row += 1
            if self.value_modify_args:
                self.set_cell_style(
                    sheet, point_row, point_col,
                    self.value_modify_args,
                    self.alignment_center, self.color_data, self.font_data)
            point_row += 1
            for _, _v in v.items():
                self.set_cell_style(
                    sheet, point_row, point_col, _v,
                    self.alignment_center, self.color_data,
                    self.font_data)
                point_row += 1
        return True


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
                                                "TCP", "TCP conn",
                                                "RPC/TCP", "RPC/UDP"
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

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        index_start_row = self.index_start
        index_start_col = self.index_start
        index_start_items = index_start_row
        text_cmd = self.text_cmd
        text_modify_args = self.text_modify_args
        text_first_cell = self.tool_name

        sheet = None
        if self.tool_name in workbook.sheetnames:  # 已存在sheet
            sheet = workbook[self.tool_name]
            index_start_col = sheet.max_column + 1
            index_start_items = 4

        else:   # 不存在sheet
            point_row = 0
            sheet = workbook.create_sheet(self.tool_name)
            sheet.column_dimensions['A'].width = self.ret_col_1_width
            sheet.column_dimensions['B'].width = self.ret_col_2_width
            # 开始
            self.set_cell_style(
                sheet, index_start_row+point_row,
                index_start_col, text_first_cell,
                self.alignment_center, self.color_title, self.font_title)
            self.merge_row_cell(sheet, index_start_row+point_row,
                                index_start_col, index_start_col+1)
            # 执行命令
            point_row += 1
            sheet.row_dimensions[index_start_row+point_row].height = 25
            self.set_cell_style(
                sheet, index_start_row+point_row, index_start_col, text_cmd,
                self.alignment_center, self.color_cmd, self.font_cmd)
            self.merge_row_cell(sheet, index_start_row+point_row,
                                index_start_col, index_start_col+1)
            # 修改参数
            point_row += 1
            sheet.row_dimensions[index_start_row +
                                 point_row].height = self.ret_row_1_height
            self.set_cell_style(
                sheet, index_start_row+2, index_start_col, text_modify_args,
                self.alignment_center, self.color_cmd, self.font_cmd)
            self.merge_row_cell(sheet, index_start_row+point_row,
                                index_start_col, index_start_col+1)
            # 填充第一列
            index_start_items = point_row + 1
            for k, v in self.items.items():
                point_row += 1
                self.set_cell_style(
                    sheet, index_start_row+point_row,
                    index_start_col, k,
                    self.alignment_center, self.color_item_1, self.font_item_1)
                if len(v) > 1:
                    # 填充第二列
                    for i, s in enumerate(v):
                        self.set_cell_style(
                            sheet, index_start_row+point_row+i,
                            index_start_col+1, s, self.alignment_center,
                            self.color_item_2, self.font_item_2)
                    self.merge_col_cell(
                        sheet, "A", index_start_row+point_row,
                        index_start_row+point_row+len(v)-1)
                    point_row += len(v)-1
            index_start_col = 3
        for i, item_list in enumerate(ret_dict["items"]):
            # 填充列头
            idx_col = index_start_col+i
            sheet.column_dimensions[utils.get_column_letter(
                idx_col)].width = self.ret_col_data_width
            self.set_cell_style(
                sheet, 1, idx_col, self.tool_name + '#'+str(idx_col-2),
                self.alignment_center, self.color_col_top,
                self.font_col_top)

            if self.value_cmd:
                self.set_cell_style(
                    sheet, 2, idx_col,
                    self.value_cmd,
                    self.alignment_center, self.color_data, self.font_data)
            if self.value_modify_args:
                self.set_cell_style(
                    sheet, 3, idx_col,
                    self.value_modify_args,
                    self.alignment_center, self.color_data, self.font_data)

            j_index = index_start_items
            for item in item_list:
                _items = list(item.values())[0]
                for _ in _items.keys():
                    j_index += 1
                    cell_key = sheet.cell(j_index, 2).value
                    self.set_cell_style(
                        sheet, j_index, idx_col, _items.get(cell_key),
                        self.alignment_center,
                        self.color_data, self.font_data)
        return True


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
            for line in _single_result.split('\n'):
                for k in self.items:
                    if k in line:
                        temp = re.findall(r"-?\d+\.?\d*e?-?\d*?", line)
                        if temp[0]:
                            ret_dict[self.thread[0]][k] = temp[0]
            # 处理多核测试结果
            for line in _multiple_result.split('\n'):
                for k in self.items:
                    if k in line:
                        temp = re.findall(r"-?\d+\.?\d*e?-?\d*?", line)
                        if temp[0]:
                            ret_dict[self.thread[1]][k] = temp[0]
            # print(ret_dict)
        if len(ret_dict.keys()) > 1:
            return ret_dict
        else:
            return None

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        index_start_row = self.index_start
        index_start_col = self.index_start
        text_cmd = self.text_cmd
        text_modify_args = self.text_modify_args
        index_start_single = index_start_row+3
        index_end_single = index_start_single + len(self.items) - 1
        index_start_max = index_end_single+4

        tlb_thread_single = []
        tlb_thread_max = []  # 存放分数数据

        if self.thread[0] in ret_dict.keys():
            tlb_thread_single = list(ret_dict[self.thread[0]].values())
        if self.thread[1] in ret_dict.keys():
            tlb_thread_max = list(ret_dict[self.thread[1]].values())

        sheet = None
        if self.tool_name in workbook.sheetnames:  # 已存在sheet
            sheet = workbook[self.tool_name]
            index_start_col = sheet.max_column + 1

        else:   # 不存在sheet
            sheet = workbook.create_sheet(self.tool_name)
            sheet.column_dimensions['A'].width = self.ret_col_1_width
            # 单线程开始
            self.set_cell_style(
                sheet, index_start_row, index_start_col, self.thread[0],
                self.alignment_center, self.color_title, self.font_title)
            # 执行命令
            sheet.row_dimensions[index_start_row+1].height = 25
            self.set_cell_style(
                sheet, index_start_row+1, index_start_col, text_cmd,
                self.alignment_center, self.color_cmd, self.font_cmd)
            # 修改参数
            sheet.row_dimensions[index_start_row +
                                 2].height = self.ret_row_1_height
            self.set_cell_style(
                sheet, index_start_row+2, index_start_col, text_modify_args,
                self.alignment_center, self.color_cmd, self.font_cmd)
            # 多线程开始
            self.set_cell_style(
                sheet, index_end_single + 1, index_start_col, self.thread[1],
                self.alignment_center, self.color_title, self.font_title)
            # 执行命令
            sheet.row_dimensions[index_end_single+1].height = 25
            self.set_cell_style(
                sheet, index_end_single+2, index_start_col, text_cmd,
                self.alignment_center, self.color_cmd, self.font_cmd)
            # 修改参数
            sheet.row_dimensions[index_end_single +
                                 2].height = self.ret_row_1_height
            self.set_cell_style(
                sheet, index_end_single+3, index_start_col, text_modify_args,
                self.alignment_center, self.color_cmd, self.font_cmd)
            for i, v in enumerate(self.items):
                self.set_cell_style(
                    sheet, index_start_single + i,
                    index_start_col, v,
                    self.alignment_left, self.color_item_1, self.font_item_1)
                self.set_cell_style(
                    sheet, index_start_max + i, index_start_col, v,
                    self.alignment_left, self.color_item_1, self.font_item_1)
            index_start_col += 1
        sheet.column_dimensions[utils.get_column_letter(
            index_start_col)].width = self.ret_col_data_width
        # 填充列头
        self.set_cell_style(
            sheet, 1, index_start_col,
            self.tool_name + '#'+str(index_start_col-1),
            self.alignment_center, self.color_col_top, self.font_col_top)
        self.set_cell_style(
            sheet, index_end_single+1, index_start_col,
            self.tool_name + '#'+str(index_start_col-1),
            self.alignment_center, self.color_col_top, self.font_col_top)

        if self.value_cmd:
            self.set_cell_style(
                sheet, index_start_row+1, index_start_col,
                self.value_cmd,
                self.alignment_center, self.color_data, self.font_data)

            self.set_cell_style(
                sheet, index_end_single+2, index_start_col,
                self.value_cmd,
                self.alignment_center, self.color_data, self.font_data)
        if self.value_modify_args:
            self.set_cell_style(
                sheet, index_start_row+2, index_start_col,
                self.value_modify_args,
                self.alignment_center, self.color_data, self.font_data)

            self.set_cell_style(
                sheet, index_end_single+3, index_start_col,
                self.value_modify_args,
                self.alignment_center, self.color_data, self.font_data)
        for i, v in enumerate(self.items):
            self.set_cell_style(
                sheet, index_start_single + i, index_start_col,
                tlb_thread_single[i].strip(" "),
                self.alignment_center, self.color_data, self.font_data)
            self.set_cell_style(
                sheet, index_start_max+i, index_start_col,
                tlb_thread_max[i].strip(" "),
                self.alignment_center, self.color_data, self.font_data)
        return True


class Netperf(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_NETPERF
        self.items = ["TCP_Stream", "UDP_Stream", "网络响应时间",
                      "TCP_CRR", "TCP_RR", "UDP_RR"]

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name}
        ret_dict['测试记录'] = []
        with open(file, 'r') as f:
            lines = f.readlines()
            for i in [7, 14, 21, 28, 36, 44]:
                ret_dict['测试记录'].append(lines[i].strip().split(' ')[-1])
        return ret_dict

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        if ret_dict['tool_name'] in workbook.sheetnames:
            sheet = workbook[ret_dict['tool_name']]
        else:
            sheet = workbook.create_sheet(ret_dict['tool_name'])
            sheet.column_dimensions['A'].width = 18.25
            for i in range(1, 10):
                sheet.row_dimensions[i].height = 34
            sheet.merge_cells('A1:A3')
            self.set_cell_style(
                sheet, 1, 1, ret_dict['tool_name'] + '\n环境参数', self.alignment_center, self.color_title, self.font_title)
            for i in range(4, 10):
                self.set_cell_style(
                    sheet, i, 1, self.items[i-4], self.alignment_center, self.color_item_1, self.font_item_1)

        column_index = len(sheet[1]) + 1
        sheet.column_dimensions[chr(ord('A')+column_index-1)].width = 18.25
        self.set_cell_style(sheet, 1, column_index, 'netperf#' + str(column_index-1),
                            self.alignment_left, self.color_col_top, self.font_col_top)
        self.set_cell_style(sheet, 2, column_index, self.text_cmd + self.value_cmd,
                            self.alignment_center, self.color_cmd, self.font_cmd)
        self.set_cell_style(sheet, 3, column_index, self.text_modify_args +
                            self.value_modify_args, self.alignment_center, self.color_cmd, self.font_cmd)
        for i in range(4, 10):
            self.set_cell_style(
                sheet, i, column_index, ret_dict['测试记录'][i-4], self.alignment_center, self.color_data, self.font_data)

        return True


class Fio(BenchMark):
    def __init__(self):
        super().__init__()
        self.tool_name = TOOL_NAME_FIO
        self.items = {"items": ["bs", "io", "iops", "bw"]}

    def ret_to_dict(self, file: str):
        ret_dict = {"tool_name": self.tool_name}
        _file_lines = None
        _rw = None
        with open(file, "r") as f:
            _file_lines = f.readlines()
        _regx = r'(?<=rw=).[a-z_]*'
        _rw = re.findall(_regx, _file_lines[0])[0]
        _regx = r'(?<=bs=\(R\)\s).[A-Z0-9_]*'
        _bs = re.findall(_regx, _file_lines[0])[0]
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

    def ret_dict_to_excel(self, workbook: Workbook, ret_dict: dict):
        index_start_row = self.index_start
        index_start_col = self.index_start
        index_start_items = index_start_row
        text_cmd = self.text_cmd
        text_modify_args = self.text_modify_args
        text_first_cell = self.tool_name

        rw = ret_dict["rw"]

        sheet = None
        if self.tool_name in workbook.sheetnames:  # 已存在sheet
            sheet = workbook[self.tool_name]
            index_start_col = sheet.max_column + 1
            index_start_items = 4
            _rw_exit = False
            for row in sheet.iter_rows(min_row=index_start_items):
                if row[0].value == rw:
                    index_start_items = row[0].row
                    _rw_exit = True
                    break
            if not _rw_exit:
                index_start_items = sheet.max_row + 1
                self.set_cell_style(
                    sheet, index_start_items, 1, rw,
                    self.alignment_center,
                    self.color_item_1, self.font_item_1)
                for i, _l in enumerate(self.items["items"]):
                    self.set_cell_style(
                        sheet, index_start_items+i, 2, _l,
                        self.alignment_center,
                        self.color_item_2, self.font_item_2)
                self.merge_col_cell(
                    sheet, "A", index_start_items, index_start_items+3)

        else:   # 不存在sheet
            sheet = workbook.create_sheet(self.tool_name)
            sheet.column_dimensions['A'].width = self.ret_col_1_width/2
            sheet.column_dimensions['B'].width = self.ret_col_2_width/2
            # 开始
            point_row = 1
            self.set_cell_style(
                sheet, point_row,
                index_start_col, text_first_cell,
                self.alignment_center, self.color_title, self.font_title)
            self.merge_row_cell(sheet, point_row,
                                index_start_col, index_start_col+1)
            # 执行命令
            point_row += 1
            sheet.row_dimensions[point_row].height = 25
            self.set_cell_style(
                sheet, point_row, index_start_col, text_cmd,
                self.alignment_center, self.color_cmd, self.font_cmd)
            self.merge_row_cell(sheet, point_row,
                                index_start_col, index_start_col+1)
            # 修改参数
            point_row += 1
            sheet.row_dimensions[point_row].height = self.ret_row_1_height
            self.set_cell_style(
                sheet, point_row, index_start_col,
                text_modify_args,
                self.alignment_center, self.color_cmd, self.font_cmd)
            self.merge_row_cell(sheet, point_row,
                                index_start_col, index_start_col+1)
            point_row += 1
            self.set_cell_style(
                sheet, point_row, 1, rw,
                self.alignment_center, self.color_item_1, self.font_item_1)
            for i, _l in enumerate(self.items["items"]):
                self.set_cell_style(
                    sheet, point_row+i, index_start_col+1, _l,
                    self.alignment_center, self.color_item_2, self.font_item_2)
            index_start_col = 3
            index_start_items = point_row

        self.merge_col_cell(sheet, "A", 4, 7)

        sheet.column_dimensions[utils.get_column_letter(
            index_start_col)].width = self.ret_col_2_width
        idx_col = index_start_col
        self.set_cell_style(
            sheet, 1, idx_col, self.tool_name + '#'+str(idx_col-2),
            self.alignment_center, self.color_col_top,
            self.font_col_top)
        if self.value_cmd:
            self.set_cell_style(
                sheet, 2, idx_col,
                self.value_cmd,
                self.alignment_center, self.color_data, self.font_data)
        if self.value_modify_args:
            self.set_cell_style(
                sheet, 3, idx_col,
                self.value_modify_args,
                self.alignment_center, self.color_data, self.font_data)
        for i, v in enumerate(ret_dict["items"].values()):
            self.set_cell_style(
                sheet, index_start_items+i,
                idx_col,
                v, self.alignment_center,
                self.color_data, self.font_data)
        return True


class ExportXlsx(object):
    def __init__(self):
        self.env_dict = None
        self.ret_dict = None
        self.tool_name = None
        self.tool_cls = None

        self.excel_name = "kytuning-result.xlsx"
        self.jsob_name = "kytuning-result.json"

    @ staticmethod
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

    @ staticmethod
    def get_tool_cls(tool_name):
        """通过工具名实例化使用的类"""
        cls_dict = {v.__name__: v for v in BenchMark.__subclasses__()}
        match_names = difflib.get_close_matches(
            tool_name, list(cls_dict.keys()), 1)
        return cls_dict.get(match_names[0])()

    def ret_to_dict(
            self, tool_name: str, ret_path: str, cmd: str, argv: str) -> list:
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

    def rets_to_dict_list(
            self, tool_name: str, ret_path: str, cmd: str, argv: str) -> list:
        ret_dict_list = []
        for file in self.get_files(ret_path):
            ret_dict = self.ret_to_dict(tool_name, file)
            if ret_dict is None:
                continue
            ret_dict_list.append(ret_dict)
        return ret_dict_list

    def write_to_xlsx(
            self, ret_dict: dict, excel_path: str):
        if not ret_dict:
            print("无结果可转化!")
            return False
        excel_file = excel_path + "/" + self.excel_name
        _ret_dict = ret_dict
        wb = None
        if os.path.isfile(excel_file):
            wb = load_workbook(excel_file)
        else:
            wb = Workbook()
            wb.remove(wb.active)
        if not self.tool_cls.ret_dict_to_excel(wb, _ret_dict):
            print("结果字典转excel失败!")
            return False
        wb.save(excel_file)
        return True

    def export_env_to_xlsx(self, env_dict: dict, excel_path: str):
        wb = None
        sheet = None
        excel_file = excel_path + "/" + self.excel_name
        env_write = BenchMark()
        if os.path.isfile(excel_file):
            wb = load_workbook(excel_file)
            if env_write.sheet_env_title in wb.sheetnames:
                sheet = wb[env_write.sheet_env_title]
        else:
            wb = Workbook()
            sheet = wb.active
            sheet.title = env_write.sheet_env_title
        env_write.env_dict_to_excel(sheet, env_dict)
        wb.save(excel_file)

    def export_ret_to_xlsx(
            self, tool_name: str, ret_path: str,
            export_path: str, cmd: str, argv: str) -> bool:
        _tool_name = tool_name.title()
        _ret_path = ret_path
        _ret_dict_list = []
        if not _tool_name or not _ret_path:
            return False
        if not os.path.exists(_ret_path):
            print("%s结果文件（路径）不存在!" % (ret_path))
            return False

        if os.path.isfile(_ret_path):
            _ret_dict_list.append(self.ret_to_dict(
                _tool_name, _ret_path, cmd, argv))
        else:
            _ret_dict_list = self.rets_to_dict_list(
                _tool_name, _ret_path, cmd, argv)
        if not _ret_dict_list:
            print("获取结果字典列表为空!")
            return False
        for _ret_dict in _ret_dict_list:
            self.write_to_xlsx(_ret_dict, export_path)
        return True


if __name__ == '__main__':
    ex = ExportXlsx()
    if 0:
        try:  # 调试env导出excel时使用
            os.remove("/home/wqs/virtul machine/Share/"+ex.excel_name)
        except Exception:
            pass
    env = 0
    if env:
        json_data = ''
        with open(
                "/home/wqs/vscode_ws/python/" +
                "kytuning/kytuning/test/export_excel/getenv.json", "r") as f:
            json_data = json.load(f)
        ex.export_env_to_xlsx(json_data, "/home/wqs/virtul machine/Share")
    else:
        tool_name = TOOL_NAME_JVM08
        path = "/home/wqs/vscode_ws/python/kytuning/kytuning/test/export_excel"
        ex.export_ret_to_xlsx(
            tool_name,
            "/home/wqs/virtul machine/Share/文件传输专用/kytuning/specjvm-demo-null-0-0",
            "/home/wqs/virtul machine/Share/文件传输专用/kytuning", '测试cmd', '测试args')
