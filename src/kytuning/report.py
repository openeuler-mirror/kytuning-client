# 
# report模块设计和实现分为三个阶段
# 1. 实现中间结果保存
# 2. 实现excel文件导出
# 3. 实现上报报文拼装
import time
import json
import os
from .exportexcel import *


__all__ = ['Report']

class Report(object):
    
    def __init__(self,basepath):
        self.basepath    = basepath
        self.resultspath = self.basepath + "/results"
        self.current_result_dir = None
        self.current_log_dir = None
        self.current_opmodify_dir = None
        self.current_testcases_dir = None
        self.current_raw_result_dir = None
        self.current_env_file = None
        self.current_report_file = None
        self.exportxlsx = ExportXlsx()
        self.all_json_file = os.path.abspath(os.path.join(self.basepath, "../../", "all_json_file.json"))

    def path_init(self):
        """
        临时文件存放路径初始化
        """
        self.current_result_dir = self.resultspath + "/" +time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        os.makedirs(self.current_result_dir,exist_ok=False)

        self.current_env_file = self.current_result_dir + "/getenv.json"

        self.current_log_dir = self.current_result_dir + "/logs"
        os.makedirs(self.current_log_dir,exist_ok=False)
        self.current_opmodify_dir = self.current_result_dir + "/opmodify"
        os.makedirs(self.current_opmodify_dir,exist_ok=False)
        self.current_testcases_dir = self.current_result_dir + "/testcases"
        os.makedirs(self.current_testcases_dir,exist_ok=False)
        self.current_raw_result_dir = self.current_result_dir + "/result"
        os.makedirs(self.current_raw_result_dir,exist_ok=False)
        self.current_report_file = self.current_result_dir     # +  "/kytuning-result.xlsx"

    def get_log_save_dir(self):
        """
        获取日志保存路径   
        :return 返回日志保存路径
        """
        return self.current_log_dir

    def save_env_data(self,env_data):
        """
        保存初始环境信息
        :param env_data      初始环境信息数据
        :return 返回保存的初始化环境信息文件路径
        """
        # 写环境信息到all_json_data文件中
        self.save_env_data_to_json(env_data)
        file = open(self.current_env_file, 'w+')
        file.write(env_data)
        file.close()

        # 保存环境信息到 xlsx 表格中
        self.exportxlsx.export_env_to_xlsx(json.loads(env_data),self.current_report_file)

        return self.current_env_file

    def save_opmodify_data(self,name,testinfo,data):
        '''
        环境调优修改信息保存        
        :param name          测试名称  
        :param testinfo      测试清单信息
        :param data          环境修改信息
        :return              返回环境修改信息文件保存路径
        '''
        # json1=json.loads(testinfo)
        file_path=self.current_opmodify_dir + "/opmodify-" + name
        file = open(file_path,'w+')
        file.write(data)
        file.close()
        return file_path

    def save_testcase_data(self,name,testinfo):
        '''
        测试清单信息保存      
        :param name          测试名称  
        :param testinfo      测试清单信息
        :param data          测试清单内容
        :return              返回测试清单信息文件保存路径
        '''
        # json1=json.loads(testinfo)
        data = json.dumps(testinfo)
        file_path=self.current_testcases_dir+"/testcase-"+ name + ".json"
        file = open(file_path,'w+')
        file.write(data)
        file.close()
        return file_path

    def save_result_data(self, name, data):
        # 保存中间结果文件
        file_path=self.current_raw_result_dir + "/" + name
        file = open(file_path,'w+')
        file.write(data)
        file.close()
        return file_path

    def save_result_json(self, name, data):
        # 保存中间结果文件
        file_path=self.current_raw_result_dir + "/" + name + ".json"
        file = open(file_path,'w+')
        jd = json.dumps(data)
        file.write(jd)
        file.close()
        return file_path


    def dumps_configs(self,testinfo):
        dumps_str=""
        global_configs = testinfo["configs"]
        test_configs = testinfo["testcase"]["configs"]

        for g_config in global_configs:
            dumps_str =dumps_str + g_config["setup"]+'\r\n'
        for t_config in test_configs:
            dumps_str = dumps_str + t_config["setup"] +'\r\n'
        return dumps_str

    def save_result(self,name,testinfo,data, only_xlsx = False):
        '''
        测试结果保存接口
        :param name          测试名称  
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              测试结果保存路径
        '''
        # json1=json.loads(testinfo)

        file_path=self.current_raw_result_dir + "/" + name

        tool_name = testinfo["test_type"]
        exec_cmd = testinfo["testcase"]["run"]
        exec_configs= self.dumps_configs(testinfo)
        if only_xlsx == False:
            # 保存中间结果文件
            self.save_result_data(name, data)

            # 保存测试清单信息
            self.save_testcase_data(name,testinfo)

            # 保存json的结果数据
            ret = self.exportxlsx.ret_to_dict(tool_name,
                        file_path,exec_cmd,exec_configs)
            print(ret)
            self.save_result_json(name,ret)

        # 保存all json的结果数据
        ret = self.exportxlsx.ret_to_dict(tool_name, file_path, exec_cmd, exec_configs)
        self.save_test_data_to_all_json(name, ret)

        # 将中间结果文件导入到 excel 表格中
        #tool_name = testinfo["test_type"]
        #exec_cmd = testinfo["testcase"]["run"]
        #exec_configs= self.dumps_configs(testinfo)

        if(type(exec_configs)== str):
            self.exportxlsx.export_ret_to_xlsx(tool_name,
                            file_path,
                            self.current_report_file,exec_cmd,exec_configs)
        else:
            self.exportxlsx.export_ret_to_xlsx(tool_name,
                            file_path,
                            self.current_report_file,exec_cmd,None)
        return file_path

    def save_unixbench_detail(self, name, tinf, result):
        path = '{tdir}/{name}'.format(tdir=self.current_result_dir, name=name)
        jobj = { 'testinfo' : tinf, 'result' : result }
        data = json.dumps(jobj)
        with open(path, 'w+') as fp:
            fp.write(data)

    
    def save_unixbench(self,name,testinfo,data):
        '''
        保存 unixnbench 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              unixbench 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_fio(self,name,testinfo,data):
        '''
        保存 fio 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              fio 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_iozone(self,name,testinfo,data):
        '''
        保存 iozone 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              iozone 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_stream(self,name,testinfo,data):
        '''
        保存 stream 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              stream 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_speccpu2006(self,name,testinfo,data):
        '''
        保存 speccpu2006 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              speccpu2006 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_speccpu2017(self,name,testinfo,data):
        '''
        保存 speccpu2017 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              speccpu2017 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_specjvm(self,name,testinfo,data):
        '''
        保存 specjvm 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              specjvm 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)
    def save_lmbench(self,name,testinfo,data):
        '''
        保存 lmbench 测试结果        
        :param testinfo      测试清单信息
        :param data          测试结果数据
        :return              lmbench 测试结果保存路径
        '''
        return self.save_result(name,testinfo,data)

    def export_result(self):
        '''
        导出测试结果        
        '''
        #print("export result data")
        return self.current_report_file
        # todo
    def export_unixbench(self):
        '''
        导出 unixnbench 测试结果
        '''
        return self.export_result()

    def export_lmbench(self):
        '''
        导出 lmbench 测试结果        
        '''
        return self.export_result()
    def export_fio(self):
        '''
        导出 fio 测试结果
        '''
        return self.export_result()
    def export_iozone(self):
        '''
        导出 iozone 测试结果
        '''
        return self.export_result()   
    def export_stream(self):
        '''
        导出 stream 测试结果
        '''
        return self.export_result() 
    def export_speccpu2006(self):
        '''
        导出 speccpu2006 测试结果
        '''
        return self.export_result() 
    def export_speccpu2017(self):
        '''
        导出 speccpu2017 测试结果
        '''
        return self.export_result() 
    def export_specjvm(self):
        '''
        导出 specjvm 测试结果
        '''
        return self.export_result()

    def save_env_data_to_json(self, env_data):
        """
        :负责人       wqz
        :message    保存初始环境信息到all_json_file.json
        :param      env_data:初始环境信息数据
        :return     all_json_file.json文件路径
        """
        time_stamp = time.time()
        env_data = env_data[:-1]+',"time":'+str(time_stamp) + '}'
        all_json_file = os.path.abspath(os.path.join(self.basepath, "../../", "all_json_file.json"))
        if not os.path.exists(all_json_file):
            with open(all_json_file, 'w+', encoding='utf-8') as f:
                f.write(env_data)
        return all_json_file

    def save_test_data_to_all_json(self, name, data):
        """
        :负责人       wqz
        :message    保存测试数据到all_json_file.json
        :param      name: 原始文件名称,区分是什么类型的数据.
        :param      data: json数据
        :return:    all_json_file.json文件路径
        """
        all_json_file = os.path.abspath(os.path.join(self.basepath, "../../", "all_json_file.json"))
        time = self.current_result_dir.split('/')[-1]
        data['time'] = time
        with open(all_json_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        content[name] = data
        with open(all_json_file, 'w+', encoding='utf-8') as f_new:
            json.dump(content, f_new)
        return all_json_file


if __name__ == '__main__':

    pwd_path = os.getcwd()
    print(pwd_path)

    # 实例化对象
    rep = Report(".")
    # 初始化对象参数
    rep.path_init()

    rep.save_env_data(time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))
    
    # only test
    file = open("./1.out",'r')
    data = file.read()
    file.close()
    tname = 'Unixbench-5.9.1-kernel.sched_migration_cost_ns-0-0'
    # testcase 示例
    tinfo_str = '{\
    "project": "Unixbench-5.9.1",\
    "test_type": "Unixbench",\
    "rpm_list": ["numactl", "jemalloc"],\
    "configs": [{\
        "name": "vm.swappiness",\
        "desc": "the vm.swapiness",\
        "setup": "sysctl -w vm.swappiness=20",\
        "reset": "sysctl -w vm.swappiness=20"\
    }],\
    "testcase": {\
        "name": "Unixbench-5.9.1-kernel.sched_migration_cost_ns-0",\
        "build": "make",\
        "clean": "make spotless",\
        "run": "./Run -c 1",\
        "configs": [{\
            "name": "kernel.sched_migration_cost_ns",\
            "desc": "context switch",\
            "setup": "sysctl -n kernel.sched_migration_cost_ns=100000",\
            "reset": "sysctl -n kernel.sched_migration_cost_ns=100000"\
        }]\
    }\
    }'
    tinfo = json.loads(tinfo_str)
    # print(json.dumps(tinfo["configs"]))
    # print(json.dumps(tinfo["testcase"]["configs"]))
    # print(rep.dumps_configs(tinfo))
    rep.save_unixbench(tname,tinfo,data)
